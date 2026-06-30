"""
SearchDocumentsTool — Sucht in einer Verinaris-Dokumenten-Sammlung.

Wird vom LLM aufgerufen, wenn Antworten aus den vorhandenen Dokumenten
benötigt werden (z.B. Pharma-Fachinformationen, HWG-Vorgaben, etc.).

Wrappt den existierenden RAG-Service (build_rag_context).
"""

from typing import Any

from app.services.rag import build_rag_context
from app.tools.base import BaseTool


class SearchDocumentsTool(BaseTool):
    """Sucht in einer Dokumenten-Sammlung nach relevanten Chunks."""

    name = "search_documents"
    description = (
        "Sucht in den Verinaris-Dokumenten-Sammlungen nach relevanten Inhalten. "
        "Gibt die wichtigsten Textstellen mit Quellenangaben zurück. "
        "Nützlich für Fragen, die auf hochgeladene Dokumente bezogen sind."
    )

    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Die Suchanfrage in natürlicher Sprache",
            },
            "collection": {
                "type": "string",
                "description": (
                    "Name der Dokumenten-Sammlung "
                    "(z.B. 'pharma', 'compliance', 'hr')"
                ),
            },
            "top_k": {
                "type": "integer",
                "description": "Anzahl Treffer (Default: 4, Max: 10)",
                "default": 4,
                "minimum": 1,
                "maximum": 10,
            },
        },
        "required": ["query", "collection"],
    }

    # Konfiguration
    requires_human_oversight = False  # Lesend, harmlos
    allowed_roles = ["admin", "compliance-officer", "pharma-referent", "user"]

    def execute(self, params: dict, user_id: int | None = None) -> dict[str, Any]:
        """
        Sucht in der angegebenen Sammlung.

        Args:
            params: {
                "query": str,        # Suchanfrage
                "collection": str,   # Sammlungs-Name
                "top_k": int,        # Optional, Default 4
            }
            user_id: ID des aufrufenden Users (für Audit-Log)

        Returns:
            {
                "query": str,                 # Echo der Suchanfrage
                "collection": str,            # Sammlung
                "results": [                  # Liste der Treffer
                    {
                        "filename": str,
                        "page": int,
                        "excerpt": str,       # Kurzer Auszug (~200 Zeichen)
                        "full_text": str,     # Voller Chunk
                        "relevance": float,   # 1.0 = perfekt, 0.0 = irrelevant
                    },
                    ...
                ],
                "summary": str,               # Zusammenfassung für LLM-Prompt
                "total_results": int,
            }
        """
        query = params["query"]
        collection = params["collection"]
        top_k = params.get("top_k", 4)

        # Bestehenden RAG-Service nutzen
        context_block, sources = build_rag_context(
            collection=collection,
            query=query,
            top_k=top_k,
        )

        # SourceReference-Liste in JSON-freundliches Format konvertieren
        results = []
        for source in sources:
            results.append({
                "filename": source.filename,
                "page": source.page,
                "excerpt": source.excerpt,
                "full_text": source.full_text,
                # distance: 0.0 = perfekt → wir konvertieren zu relevance (1.0 = perfekt)
                "relevance": round(1.0 - min(source.distance, 1.0), 3),
            })

        return {
            "query": query,
            "collection": collection,
            "results": results,
            "summary": context_block,
            "total_results": len(results),
        }
