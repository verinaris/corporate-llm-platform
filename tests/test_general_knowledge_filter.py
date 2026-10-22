"""Tests: kein Allgemeinwissen im Modus mit Wissensbibliothek."""

from app.services.rag import GENERAL_KNOWLEDGE_NOTICE, RAG_INSTRUCTION, strip_general_knowledge


def test_absatz_mit_doppelpunkt_wird_entfernt():
    t = ("Die AO regelt das Besteuerungsverfahren. [Quelle 1]\n\n"
         "Allgemeines Wissen (nicht aus Ihren Quellen): Die AO ist ein wichtiges Instrument.")
    out, removed = strip_general_knowledge(t)
    assert removed
    assert "wichtiges Instrument" not in out
    assert out.startswith("Die AO regelt")
    assert out.endswith(GENERAL_KNOWLEDGE_NOTICE)


def test_markdown_ueberschrift_mit_mehreren_absaetzen():
    t = "Antwort. [Quelle 1]\n\n### Allgemeines Wissen\n\nSatz A.\n\nSatz B."
    out, removed = strip_general_knowledge(t)
    assert removed and "Satz A" not in out and "Satz B" not in out


def test_fett_und_folgende_ueberschrift_bleibt():
    t = "Antwort.\n\n**Allgemeinwissen:**\nZusatz.\n\n## Fazit\nBleibt stehen."
    out, removed = strip_general_knowledge(t)
    assert removed and "Zusatz" not in out and "Bleibt stehen" in out


def test_ohne_abschnitt_unveraendert():
    t = "Nur Quellenwissen. [Quelle 2]"
    assert strip_general_knowledge(t) == (t, False)


def test_wort_mitten_im_satz_bleibt():
    t = "Das ist kein allgemeines Wissen, sondern steht in Quelle 1."
    assert strip_general_knowledge(t) == (t, False)


def test_regel_7_ist_verbot():
    assert "NIEMALS allgemeines Wissen" in RAG_INSTRUCTION
