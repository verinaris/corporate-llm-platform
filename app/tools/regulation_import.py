"""
RegulationImportTool — importiert eine oeffentliche Regulierungsquelle per URL
in die Wissensdatenbank. Erste konkrete Automation auf dem AutomationTool.

Zweistufig (Human-in-the-Loop, Freigabepflicht unabschaltbar):
    generate() : URL holen -> Text -> lokale Zusammenfassung. Erzeugt NUR einen
                 Entwurf (draft), legt noch NICHTS ab. Nebenwirkungsfrei.
    execute()  : legt den (freigegebenen) Originaltext gechunkt in die
                 Wissensdatenbank -- ueber denselben Weg wie der Datei-Upload.

Souveraen: Zusammenfassung laeuft LOKAL (qwen). Kein Cloud-Parameter (bewusst,
siehe Architektur-Grundsatzfrage Datenresidenz). Login-geschuetzte Quellen
werden nicht unterstuetzt -- fetch_clean_text scheitert dann ehrlich.
"""

from __future__ import annotations

from typing import Any

from app.llm.ollama_client import OllamaClient
from app.schemas import ChatMessage
from app.services.document_processor import (
    _chunk_text,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
)
from app.services.document_store import get_document_store
from app.services.web_fetch import (
    fetch_clean_text,
    LoginRequiredError,
    WebFetchError,
)
from app.tools.automation_base import AutomationTool

_LOCAL_MODEL = "qwen2.5:7b"
_SUMMARY_MAX_TOKENS = 700
# Wieviel Quelltext wir dem lokalen Modell fuer die Zusammenfassung geben.
# qwen2.5:7b hat begrenzten Kontext -- lieber der Anfang gut als alles schlecht.
_SUMMARY_INPUT_LIMIT = 6000


class RegulationImportTool(AutomationTool):
    name = "regulation_import"
    description = (
        "Importiert eine oeffentlich zugaengliche Regulierungsquelle (z.B. eine "
        "EMA- oder EUR-Lex-Seite) per URL: holt den Text, erstellt eine "
        "Zusammenfassung zur Pruefung und legt die Quelle nach Freigabe in einer "
        "Wissenssammlung ab."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "URL der oeffentlichen Regulierungsseite (http/https).",
            },
            "collection": {
                "type": "string",
                "description": "Ziel-Wissenssammlung, in die die Quelle abgelegt wird.",
            },
        },
        "required": ["url", "collection"],
    }
    # Wer die Automation ausloesen/freigeben darf -- dieselben Rollen wie can_approve.
    allowed_roles = ("admin", "compliance-officer", "qualified-reviewer")

    async def generate(self, params: dict, user_id: int | None = None) -> dict[str, Any]:
        """Holt die Quelle und erzeugt eine pruefbare Zusammenfassung (kein Ablegen)."""
        url = (params.get("url") or "").strip()
        collection = (params.get("collection") or "").strip()
        if not url or not collection:
            return {"draft": None, "meta": {"error": "url und collection sind Pflicht."}}

        # 1. Quelle holen -- Login/Fehler kommen als klare Meldung zurueck.
        try:
            fetched = fetch_clean_text(url)
        except LoginRequiredError as exc:
            return {"draft": None, "meta": {"error": str(exc), "url": url, "login_required": True}}
        except WebFetchError as exc:
            return {"draft": None, "meta": {"error": str(exc), "url": url}}

        text = fetched["text"]
        title = fetched["title"]

        # 2. Lokale Zusammenfassung (souveraen). Nur der Anfang, s. Kontextgrenze.
        prompt = (
            "Fasse den folgenden Regulierungstext sachlich und praezise auf "
            "Deutsch zusammen. Nenne die wichtigsten Punkte in Stichpunkten. "
            "Erfinde nichts, was nicht im Text steht.\n\n"
            f"TITEL: {title}\n\nTEXT:\n{text[:_SUMMARY_INPUT_LIMIT]}"
        )
        client = OllamaClient()
        try:
            resp = await client.chat(
                messages=[ChatMessage(role="user", content=prompt)],
                model=_LOCAL_MODEL,
                max_tokens=_SUMMARY_MAX_TOKENS,
            )
            summary = resp.content
        except Exception as exc:  # Modell nicht erreichbar o.ae. -- Entwurf ohne Summary
            summary = None
            return {
                "draft": None,
                "meta": {
                    "error": f"Zusammenfassung fehlgeschlagen: {exc}",
                    "url": url, "title": title, "length": fetched["length"],
                },
            }

        return {
            "draft": summary,
            "meta": {
                "url": url,
                "title": title,
                "length": fetched["length"],
                "collection": collection,
                "model": _LOCAL_MODEL,
                "note": (
                    "Zusammenfassung durch lokales Modell erstellt und vor Ablage "
                    "fachlich zu pruefen. Bei Freigabe wird der VOLLTEXT der Quelle "
                    "(nicht die Zusammenfassung) in die Wissenssammlung gechunkt."
                ),
            },
        }

    async def execute(self, params: dict, user_id: int | None = None) -> dict[str, Any]:
        """Legt den freigegebenen Volltext gechunkt in die Wissenssammlung ab."""
        url = (params.get("url") or "").strip()
        collection = (params.get("collection") or "").strip()
        if not url or not collection:
            return {"ok": False, "error": "url und collection sind Pflicht."}

        # Quelle erneut holen (Entwurf hielt nur die Zusammenfassung, nicht den
        # Volltext -- so bleibt generate() schlank und wir legen frischen Stand ab).
        try:
            fetched = fetch_clean_text(url)
        except (LoginRequiredError, WebFetchError) as exc:
            return {"ok": False, "error": str(exc), "url": url}

        chunks = _chunk_text(fetched["text"], DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP)
        if not chunks:
            return {"ok": False, "error": "Kein indexierbarer Text gefunden.", "url": url}

        # Ueber denselben Store wie der Datei-Upload ablegen. Als document_id nutzen
        # wir einen stabilen Hash der URL (kein DB-Document-Eintrag noetig fuers MVP).
        doc_ref = abs(hash(url)) % (10**9)
        ids = [f"web-{doc_ref}-chunk-{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "document_id": doc_ref,
                "filename": fetched["title"][:120] or url,
                "source_url": url,
                "chunk_index": i,
            }
            for i in range(len(chunks))
        ]
        get_document_store().add_chunks(collection, ids, chunks, metadatas)

        return {
            "ok": True,
            "url": url,
            "collection": collection,
            "chunks": len(chunks),
            "title": fetched["title"],
        }
