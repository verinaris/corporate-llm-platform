"""
ChromaDB-Wrapper.

ChromaDB ist eine lokale Vektor-Datenbank. Sie speichert:
- Text-Chunks
- Deren Embeddings (Vektoren)
- Beliebige Metadaten pro Chunk

Sammlungen ("Collections") sind benannte Container — wir nutzen sie als
fachliche Trennung (z.B. "pharma-fachinfos", "hr-handbuch").

Analogie: Bibliothek mit thematischen Regalen. Jedes Regal hat ein Schild
(Collection-Name). Bücher (Dokumente) werden in Seiten (Chunks) zerlegt
und am richtigen Regal abgelegt. Beim Suchen findet ChromaDB die ähnlichsten
Seiten — auch wenn die Wörter nicht 1:1 stimmen.
"""

import logging
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

# ChromaDB hat einen bekannten Bug mit der posthog-Telemetrie: trotz
# anonymized_telemetry=False werden Events versucht und scheitern dann
# an einem Signatur-Mismatch. Das ist harmlos, aber laut. Wir schalten
# das spezifische Logging stumm.
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)


# Default-Embedder ist all-MiniLM-L6-v2 (~80MB, lädt beim ersten Aufruf)
# Wird lokal ausgeführt — keine externen API-Calls.

class DocumentStore:
    """Wrapper um ChromaDB für die Plattform."""

    def __init__(self, persist_path: str = "./data/chroma"):
        Path(persist_path).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=persist_path,
            settings=ChromaSettings(
                anonymized_telemetry=False,  # DSGVO
                allow_reset=False,           # Schutz vor versehentlichem Löschen
            ),
        )

    # ------------------------------------------------------------------ #
    # Collection-Handling
    # ------------------------------------------------------------------ #

    def get_or_create_collection(self, name: str) -> Any:
        """Holt eine Collection (legt sie an, falls noch nicht vorhanden)."""
        return self._client.get_or_create_collection(name=name)

    def list_collections(self) -> list[str]:
        """Namen aller Collections."""
        return [c.name for c in self._client.list_collections()]

    def delete_collection(self, name: str) -> None:
        try:
            self._client.delete_collection(name=name)
        except Exception:
            # Collection existierte nicht — ignorieren
            pass

    # ------------------------------------------------------------------ #
    # Add / Delete
    # ------------------------------------------------------------------ #

    def add_chunks(
        self,
        collection_name: str,
        ids: list[str],
        texts: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Fügt Chunks samt Embeddings (automatisch erzeugt) hinzu."""
        coll = self.get_or_create_collection(collection_name)
        coll.add(ids=ids, documents=texts, metadatas=metadatas)

    def delete_by_document_id(
        self, collection_name: str, document_id: int
    ) -> int:
        """Löscht alle Chunks eines bestimmten Dokuments. Liefert Anzahl."""
        coll = self.get_or_create_collection(collection_name)
        # ChromaDB unterstützt Where-Filter beim Löschen
        before = coll.count()
        coll.delete(where={"document_id": document_id})
        after = coll.count()
        return before - after

    # ------------------------------------------------------------------ #
    # Query
    # ------------------------------------------------------------------ #

    def query(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Sucht die ähnlichsten Chunks zu einer Query.

        Liefert Liste von Dicts mit: text, metadata, distance.
        """
        coll = self.get_or_create_collection(collection_name)
        if coll.count() == 0:
            return []

        results = coll.query(
            query_texts=[query_text],
            n_results=min(n_results, coll.count()),
        )

        hits: list[dict[str, Any]] = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for text, meta, dist in zip(documents, metadatas, distances):
            hits.append({
                "text": text,
                "metadata": meta or {},
                "distance": float(dist),
            })
        return hits

    # ------------------------------------------------------------------ #
    # Stats
    # ------------------------------------------------------------------ #

    def collection_chunk_count(self, collection_name: str) -> int:
        try:
            return self.get_or_create_collection(collection_name).count()
        except Exception:
            return 0


# Singleton — eine Instanz für die App
_store: DocumentStore | None = None


def get_document_store() -> DocumentStore:
    global _store
    if _store is None:
        _store = DocumentStore()
    return _store
