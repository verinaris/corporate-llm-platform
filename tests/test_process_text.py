"""Tests für den Text-Eingang (Second Brain)."""

from app.services.document_processor import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    process_text,
)


def test_kurzer_text_ein_chunk_ohne_seite():
    result = process_text("Eine kurze Notiz.")
    assert result.page_count == 0
    assert len(result.chunks) == 1
    assert result.chunks[0].page == 0
    assert result.chunks[0].chunk_index == 0


def test_leerer_text_keine_chunks():
    assert process_text("   \n\t  ").chunks == []
    assert process_text("").chunks == []


def test_langer_text_wird_ueberlappend_zerlegt():
    text = "abcdefghij" * 300  # 3000 Zeichen
    result = process_text(text)
    assert len(result.chunks) > 1
    assert all(len(c.text) <= DEFAULT_CHUNK_SIZE for c in result.chunks)
    # Überlappung: Ende von Chunk 0 taucht am Anfang von Chunk 1 auf
    assert result.chunks[0].text[-DEFAULT_CHUNK_OVERLAP:] == result.chunks[1].text[:DEFAULT_CHUNK_OVERLAP]
    assert [c.chunk_index for c in result.chunks] == list(range(len(result.chunks)))


def test_whitespace_wird_normalisiert():
    result = process_text("Zeile   eins\n\n\nZeile    zwei")
    assert result.chunks[0].text == "Zeile eins\nZeile zwei"
