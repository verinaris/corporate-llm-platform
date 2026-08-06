"""
Audit-Logging Service (Phase 6a — Compliance).

Zentraler Einstiegspunkt für alle Module: `audit.log(...)`.

**Designprinzipien:**
- **Best-effort**: Audit-Fehler darf NIEMALS die Hauptaktion abbrechen
- **Synchron, aber leichtgewichtig**: SQLite-Insert, kein async-Overhead
- **Strukturiert**: `details` als JSON-String (zukunftssicher für Reporting)
- **DSGVO-bewusst**: keine sensiblen Inhalte loggen (z.B. Chat-Nachrichten);
  nur Metadaten (User, Aktion, Target-ID, optional kleiner Kontext)
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from app.database import engine
from app.models import AuditAction, AuditLog

_log = logging.getLogger(__name__)


def _compute_entry_hash(entry: AuditLog, prev_hash: Optional[str]) -> str:
    """
    Deterministischer SHA-256 ueber den unveraenderlichen Inhalt eines
    Eintrags PLUS den Hash des vorherigen Eintrags. Dadurch haengen die
    Eintraege wie Kettenglieder zusammen -- eine nachtraegliche Aenderung
    bricht die Kette am Folgeeintrag.

    Wichtig: nur stabile Felder, in fester Reihenfolge. timestamp als
    ISO-String, damit die Berechnung reproduzierbar bleibt.
    """
    ts = entry.timestamp
    if ts.tzinfo is None:
        # aus der DB naiv gelesen -> als UTC interpretieren (so wurde geschrieben)
        _ts_normalisiert = ts.replace(tzinfo=timezone.utc).isoformat()
    else:
        _ts_normalisiert = ts.astimezone(timezone.utc).isoformat()

    teile = [
        prev_hash or "",
        _ts_normalisiert,
        entry.user_email or "",
        entry.user_role or "",
        entry.action.value if hasattr(entry.action, "value") else str(entry.action),
        entry.target_type or "",
        entry.target_id or "",
        entry.details or "",
        entry.ip_address or "",
        entry.user_agent or "",
        "1" if entry.success else "0",
    ]
    roh = "|".join(teile)
    return hashlib.sha256(roh.encode("utf-8")).hexdigest()


def _last_entry_hash(session: Session) -> Optional[str]:
    """Holt den entry_hash des juengsten Eintrags (das Kettenende)."""
    stmt = select(AuditLog).order_by(AuditLog.id.desc()).limit(1)
    last = session.exec(stmt).first()
    return last.entry_hash if last else None


def log(
    user_email: str,
    action: AuditAction,
    *,
    user_role: str = "unknown",
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    success: bool = True,
    session: Optional[Session] = None,
) -> None:
    """
    Loggt eine compliance-relevante Aktion.

    **Best-effort**: schlägt das Logging fehl, wird das geloggt aber
    NICHT geworfen — die Haupt-Aktion soll NIE durch Audit-Fehler
    blockiert werden.

    Args:
        user_email: Wer die Aktion ausgeführt hat (auch pseudonymisiert OK)
        action: Aus AuditAction-Enum
        user_role: Rolle zum Zeitpunkt (für historische Korrektheit)
        target_type: Optional, z.B. "document", "plan", "user"
        target_id: Optional, ID des betroffenen Objekts
        details: Optional, dict — wird zu JSON serialisiert
        ip_address: Optional, Quell-IP
        user_agent: Optional, Browser-/Client-ID
        success: True bei erfolgreicher Aktion
        session: Optional, eigene DB-Session (sonst neue)
    """
    try:
        entry = AuditLog(
            timestamp=datetime.now(timezone.utc),
            user_email=user_email or "anonymous",
            user_role=user_role,
            action=action,
            target_type=target_type,
            target_id=str(target_id) if target_id else None,
            details=json.dumps(details, ensure_ascii=False) if details else None,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
        )
        if session is not None:
            entry.prev_hash = _last_entry_hash(session)
            entry.entry_hash = _compute_entry_hash(entry, entry.prev_hash)
            session.add(entry)
            session.commit()
        else:
            with Session(engine) as s:
                entry.prev_hash = _last_entry_hash(s)
                entry.entry_hash = _compute_entry_hash(entry, entry.prev_hash)
                s.add(entry)
                s.commit()
    except Exception as exc:
        # NIEMALS werfen — Audit darf Hauptaktion nicht abbrechen
        _log.error(
            "Audit-Log fehlgeschlagen für %s/%s: %s",
            user_email, action.value, exc,
        )


def verify_chain(session: Optional[Session] = None) -> dict:
    """
    Prueft die Integritaet der Audit-Kette (LOG-01/02).

    Laeuft alle Eintraege in Insert-Reihenfolge (id) durch und rechnet fuer
    jeden den entry_hash neu. Stimmt er nicht mit dem gespeicherten ueberein,
    wurde der Eintrag nachtraeglich veraendert. Bricht die prev_hash-Verkettung,
    wurde ein Eintrag eingefuegt oder geloescht.

    Alt-Eintraege ohne entry_hash (aus der Zeit vor der Hash-Kette) werden
    uebersprungen -- die Kette beginnt beim ersten gehashten Eintrag.

    Returns:
        {
            "ok": bool,               # True = Kette unversehrt
            "checked": int,           # Anzahl gepruefter (gehashter) Eintraege
            "skipped_legacy": int,    # Alt-Eintraege ohne Hash
            "broken_at_id": int|None, # ID des ersten gebrochenen Eintrags
            "reason": str|None,
        }
    """
    def _run(s: Session) -> dict:
        stmt = select(AuditLog).order_by(AuditLog.id.asc())
        eintraege = list(s.exec(stmt))

        checked = 0
        skipped = 0
        prev = None  # erwarteter prev_hash des naechsten gehashten Eintrags

        for e in eintraege:
            if e.entry_hash is None:
                skipped += 1
                continue

            # Verkettung pruefen (ausser beim ersten gehashten Eintrag)
            if checked > 0 and e.prev_hash != prev:
                return {
                    "ok": False, "checked": checked, "skipped_legacy": skipped,
                    "broken_at_id": e.id,
                    "reason": "prev_hash passt nicht zum vorherigen Eintrag "
                              "(Eintrag eingefuegt, geloescht oder umsortiert).",
                }

            # Inhalt pruefen: entry_hash neu berechnen
            neu = _compute_entry_hash(e, e.prev_hash)
            if neu != e.entry_hash:
                return {
                    "ok": False, "checked": checked, "skipped_legacy": skipped,
                    "broken_at_id": e.id,
                    "reason": "entry_hash stimmt nicht -- Eintrag wurde "
                              "nachtraeglich veraendert.",
                }

            prev = e.entry_hash
            checked += 1

        return {
            "ok": True, "checked": checked, "skipped_legacy": skipped,
            "broken_at_id": None, "reason": None,
        }

    if session is not None:
        return _run(session)
    with Session(engine) as s:
        return _run(s)


def purge_expired(retention_days: Optional[int] = None,
                  session: Optional[Session] = None) -> dict:
    """
    Loescht Audit-Eintraege, die aelter als die Aufbewahrungsdauer sind.

    retention_days: ueberschreibt den Settings-Default (audit_retention_days).
    Gibt zurueck, wie viele Eintraege geloescht wurden und ab welchem Datum.

    HINWEIS zur Hash-Kette: Werden alte Eintraege am ANFANG der Kette entfernt,
    bleibt die Kette der juengeren Eintraege in sich gueltig -- verify_chain
    beginnt einfach beim ersten verbliebenen gehashten Eintrag. Das Loeschen
    am KettenANFANG bricht die Verkettung der verbleibenden Eintraege nicht.
    """
    from datetime import timedelta
    from app.config import get_settings

    days = retention_days if retention_days is not None else get_settings().audit_retention_days
    grenze = datetime.now(timezone.utc) - timedelta(days=days)

    def _run(s: Session) -> dict:
        alte = list(s.exec(select(AuditLog).where(AuditLog.timestamp < grenze)))
        anzahl = len(alte)
        for e in alte:
            s.delete(e)
        s.commit()
        return {"deleted": anzahl, "cutoff": grenze.isoformat(), "retention_days": days}

    if session is not None:
        return _run(session)
    with Session(engine) as s:
        return _run(s)
