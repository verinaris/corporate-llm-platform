"""
Datenbank-Setup (SQLite via SQLModel).

Erzeugt die Tabellen beim Start, falls sie noch nicht existieren.
Liefert eine Session, mit der die App auf die DB zugreift.

Analogie: `engine` ist die Türklinke zur DB, `session` ist ein
einzelner Besuch im Archivraum.
"""

import os
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings

settings = get_settings()

# Sicherstellen, dass der data/-Ordner existiert (bei SQLite-File-DB)
if settings.database_url.startswith("sqlite:///"):
    db_path = settings.database_url.replace("sqlite:///", "")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

# Engine = DB-Verbindungspool
engine = create_engine(
    settings.database_url,
    echo=False,  # auf True setzen, um SQL-Queries zu loggen (Debug)
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)


def init_db() -> None:
    """Erzeugt alle Tabellen, die als SQLModel definiert sind."""
    # Wichtig: Modelle importieren, damit SQLModel sie kennt
    from app import models  # noqa: F401

    SQLModel.metadata.create_all(engine)
    _run_lightweight_migrations()


def _run_lightweight_migrations() -> None:
    """
    Inline-Migrationen für kleine Schema-Änderungen.

    SQLModel/SQLAlchemy `create_all()` legt neue Tabellen an, aber ergänzt
    KEINE neuen Spalten in existierenden Tabellen. Für jetzt reichen
    handgemachte ALTER-Statements; eine echte Alembic-Migration kommt mit
    Phase 6 (Deployment).
    """
    if not settings.database_url.startswith("sqlite"):
        # Andere DBs (PostgreSQL etc.) bekommen später Alembic
        return

    with engine.connect() as conn:
        # Aktuelle Spalten der documents-Tabelle
        result = conn.exec_driver_sql("PRAGMA table_info(documents)")
        existing_cols = {row[1] for row in result}

        if "content_hash" not in existing_cols:
            conn.exec_driver_sql(
                "ALTER TABLE documents ADD COLUMN content_hash TEXT"
            )
            conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_documents_content_hash "
                "ON documents(content_hash)"
            )
            conn.commit()
            print("[Migration] documents.content_hash hinzugefügt")

    # Backfill: bestehende Dokumente bekommen ihren Hash nachträglich
    _backfill_content_hashes()


def _backfill_content_hashes() -> None:
    """
    Berechnet content_hash für alle Document-Einträge, die noch keinen haben.

    Wichtig: bestehende Dateien aus Zeiten vor der Duplikatsprüfung haben
    content_hash=NULL — sonst würden Re-Uploads dieser Files NICHT als
    Duplikate erkannt. Wir lesen die Originaldatei vom Disk und berechnen
    den SHA-256 nachträglich.

    Defensiv: Wenn das Model-Feld nicht existiert (älterer Code-Stand),
    wird übersprungen statt zu crashen. Beim Server-Start soll nichts
    den ganzen Hochfahrprozess kippen.
    """
    import hashlib
    from pathlib import Path

    from sqlmodel import Session, select

    from app.models import Document

    # Defensiv: Feld muss im Modell existieren
    if not hasattr(Document, "content_hash"):
        print(
            "[Backfill] Document.content_hash fehlt im Modell — "
            "Backfill übersprungen. (Patch nicht komplett?)"
        )
        return

    try:
        with Session(engine) as session:
            rows = session.exec(
                select(Document).where(Document.content_hash.is_(None))
            ).all()

            if not rows:
                return

            updated = 0
            skipped = 0
            for doc in rows:
                if not doc.stored_path:
                    skipped += 1
                    continue
                path = Path(doc.stored_path)
                if not path.exists():
                    skipped += 1
                    continue
                try:
                    doc.content_hash = hashlib.sha256(path.read_bytes()).hexdigest()
                    session.add(doc)
                    updated += 1
                except Exception as exc:
                    print(f"[Backfill] Konnte Hash für Doc {doc.id} nicht berechnen: {exc}")
                    skipped += 1

            if updated:
                session.commit()
                print(
                    f"[Migration] {updated} bestehende Dokument(e) nachträglich gehashed"
                    + (f" ({skipped} übersprungen)" if skipped else "")
                )
    except Exception as exc:
        # Letzter Fallschirm — Backfill darf NIE den App-Start verhindern
        print(f"[Backfill] Übersprungen wegen Fehler: {exc}")


def get_session():
    """FastAPI-Dependency für DB-Session."""
    with Session(engine) as session:
        yield session
