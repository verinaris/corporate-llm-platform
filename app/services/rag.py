"""
RAG-Helper (Phase 3b).

Verbindet ChromaDB-Suche mit Chat: holt relevante Chunks zu einer Frage,
formatiert sie als Kontext für Claude und gibt strukturierte Quellen
zurück.

Analogie: Ein Bibliothekar, der vor jeder Frage in die Regale schaut,
die passenden Karteikarten heraussucht und sie dem Berater (Claude) mit
auf den Tisch legt. Der Berater zitiert daraus und vermerkt die Quelle.
"""

from app.schemas import ChatMessage, SourceReference
from app.services.document_store import get_document_store


# Hinweis, der Claude bei jeder RAG-Anfrage mitbekommt
RAG_INSTRUCTION = """\
Du beantwortest die folgende Frage AUF BASIS des unten gelieferten Kontexts \
aus der Wissensbibliothek des Nutzers. Wichtig:

1. Stütze deine Antwort PRIMÄR auf den gelieferten Kontext.
2. Wenn der Kontext die Frage nicht hinreichend beantwortet, sage das offen.
3. Erfinde KEINE Quellen, die nicht im Kontext stehen.
4. Du kannst Quellen inline kennzeichnen mit z.B. „[Quelle 1]" oder \
   „laut der Fachinformation auf Seite 3".
5. Antworte präzise und gib bei Bedarf die Seitenzahl der Quelle an.
"""


def build_rag_context(
    collection: str,
    query: str,
    top_k: int = 4,
) -> tuple[str, list[SourceReference]]:
    """
    Sucht relevante Chunks und baut daraus einen Kontext-Block.

    Returns:
        (context_block, sources) — context_block ist ein String mit allen
        Chunks fürs LLM, sources ist die strukturierte Liste für die UI.
    """
    store = get_document_store()
    raw_hits = store.query(collection, query, n_results=top_k)

    if not raw_hits:
        return "", []

    # Quellen strukturiert sammeln
    sources: list[SourceReference] = []
    context_blocks: list[str] = []

    for idx, hit in enumerate(raw_hits, start=1):
        meta = hit.get("metadata") or {}
        text = hit.get("text", "")
        distance = hit.get("distance", 0.0)

        filename = str(meta.get("filename", "?"))
        page = int(meta.get("page", 0))
        document_id = int(meta.get("document_id", 0))

        # Kurzer Auszug für die UI-Card (erste 200 Zeichen)
        excerpt = text[:200].strip()
        if len(text) > 200:
            excerpt += "…"

        sources.append(
            SourceReference(
                document_id=document_id,
                filename=filename,
                page=page,
                excerpt=excerpt,
                full_text=text,
                distance=distance,
            )
        )

        context_blocks.append(
            f"[Quelle {idx}: {filename}, Seite {page}]\n{text}"
        )

    context = "\n\n---\n\n".join(context_blocks)
    return context, sources


def inject_rag_context(
    messages: list[ChatMessage],
    context: str,
) -> list[ChatMessage]:
    """
    Fügt den RAG-Kontext und die Anweisung als zusätzliche System-Message
    vor die letzte User-Nachricht ein.

    Wenn schon ein Branchen-System-Prompt vorne steht, hängt sich der
    RAG-Block dahinter an — als zweite System-Message.
    """
    if not context:
        return messages

    rag_message = ChatMessage(
        role="system",
        content=(
            f"{RAG_INSTRUCTION}\n\n"
            f"=== KONTEXT AUS WISSENSBIBLIOTHEK ===\n\n"
            f"{context}\n\n"
            f"=== ENDE KONTEXT ===\n"
        ),
    )

    # System-Messages aller Art sammeln, dann übrige
    system_msgs: list[ChatMessage] = []
    other_msgs: list[ChatMessage] = []
    for m in messages:
        if m.role == "system":
            system_msgs.append(m)
        else:
            other_msgs.append(m)

    return system_msgs + [rag_message] + other_msgs


def extract_last_user_query(messages: list[ChatMessage]) -> str:
    """Holt die letzte User-Nachricht — das ist die Frage, die wir suchen."""
    for m in reversed(messages):
        if m.role == "user":
            return m.content
    return ""
