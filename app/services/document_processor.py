"""
Document-Processor.

Verarbeitet ein hochgeladenes PDF:
1. Liest jede Seite mit pypdf
2. Zerlegt den Text in überlappende Chunks
3. Bereitet die Daten zum Speichern in ChromaDB vor

Analogie: Wie ein Verlagsmitarbeiter, der ein Buch entgegennimmt, jede
Seite kopiert und in handliche Abschnitte schneidet. Jeder Abschnitt
bekommt einen Aufkleber mit "aus welchem Buch, welcher Seite".
"""

import io
from dataclasses import dataclass

import pypdf


# Standardwerte fürs Chunking — bewährt für deutsche Fachtexte
DEFAULT_CHUNK_SIZE = 800       # Zeichen pro Chunk
DEFAULT_CHUNK_OVERLAP = 120    # Überlappung zwischen Chunks


@dataclass
class ProcessedChunk:
    """Ein Chunk mit allen Metadaten."""

    text: str
    page: int
    chunk_index: int


@dataclass
class ProcessedDocument:
    """Ergebnis der PDF-Verarbeitung."""

    page_count: int
    chunks: list[ProcessedChunk]


def process_pdf(
    file_bytes: bytes,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> ProcessedDocument:
    """
    Liest ein PDF und zerlegt es in Chunks.

    Jeder Chunk weiß, von welcher Seite er kommt.
    """
    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    page_count = len(reader.pages)
    chunks: list[ProcessedChunk] = []
    chunk_index = 0

    for page_num, page in enumerate(reader.pages, start=1):
        try:
            page_text = page.extract_text() or ""
        except Exception:
            page_text = ""

        page_text = _normalize_whitespace(page_text)
        if not page_text.strip():
            continue

        for chunk in _chunk_text(page_text, chunk_size, chunk_overlap):
            chunks.append(
                ProcessedChunk(
                    text=chunk,
                    page=page_num,
                    chunk_index=chunk_index,
                )
            )
            chunk_index += 1

    return ProcessedDocument(page_count=page_count, chunks=chunks)


# ----------------------------------------------------------------------- #
# Helpers
# ----------------------------------------------------------------------- #

def _normalize_whitespace(text: str) -> str:
    """Vereinheitlicht Whitespace ohne den Inhalt zu zerstören."""
    # Mehrfache Leerzeichen/Tabs → einzelnes Leerzeichen
    # Aber Zeilenumbrüche behalten (helfen beim Sinn-Erkennen)
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _chunk_text(
    text: str, chunk_size: int, overlap: int
) -> list[str]:
    """Zerlegt Text in überlappende Chunks fester Größe."""
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    step = max(1, chunk_size - overlap)
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start += step
    return chunks
