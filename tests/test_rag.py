"""Tests für die RAG-Helper (Phase 3b)."""

from app.schemas import ChatMessage, SourceReference
from app.services.rag import (
    RAG_INSTRUCTION,
    extract_last_user_query,
    inject_rag_context,
)


# ============================================================ #
# extract_last_user_query
# ============================================================ #

def test_extract_last_user_query_from_single():
    msgs = [ChatMessage(role="user", content="Was ist Ibuprofen?")]
    assert extract_last_user_query(msgs) == "Was ist Ibuprofen?"


def test_extract_last_user_query_from_conversation():
    msgs = [
        ChatMessage(role="user", content="Frage 1"),
        ChatMessage(role="assistant", content="Antwort 1"),
        ChatMessage(role="user", content="Frage 2"),
        ChatMessage(role="assistant", content="Antwort 2"),
        ChatMessage(role="user", content="Frage 3"),
    ]
    assert extract_last_user_query(msgs) == "Frage 3"


def test_extract_last_user_query_empty():
    assert extract_last_user_query([]) == ""


def test_extract_ignores_system_messages():
    msgs = [
        ChatMessage(role="system", content="Du bist Pharma-Assistent"),
        ChatMessage(role="user", content="Echte Frage"),
        ChatMessage(role="assistant", content="Antwort"),
    ]
    assert extract_last_user_query(msgs) == "Echte Frage"


# ============================================================ #
# inject_rag_context
# ============================================================ #

def test_inject_with_empty_context_returns_unchanged():
    msgs = [ChatMessage(role="user", content="Frage")]
    assert inject_rag_context(msgs, "") == msgs


def test_inject_prepends_system_message():
    msgs = [ChatMessage(role="user", content="Frage zu Wechselwirkungen")]
    context = "[Quelle 1]\nWechselwirkungen: ..."
    out = inject_rag_context(msgs, context)

    # Erste Nachricht muss System sein, mit RAG-Instruktion
    assert out[0].role == "system"
    assert "KONTEXT" in out[0].content
    assert context in out[0].content
    assert RAG_INSTRUCTION.strip()[:30] in out[0].content
    # Original-User-Message bleibt erhalten
    assert out[-1] == msgs[0]


def test_inject_keeps_existing_system_prompt():
    """Branchen-Prompt vorne, RAG-Block direkt danach."""
    msgs = [
        ChatMessage(role="system", content="Pharma-Compliance"),
        ChatMessage(role="user", content="Frage"),
    ]
    out = inject_rag_context(msgs, "[Quelle 1]\nDaten...")

    assert out[0].role == "system"
    assert "Pharma-Compliance" in out[0].content
    assert out[1].role == "system"
    assert "KONTEXT" in out[1].content
    assert out[-1].role == "user"
