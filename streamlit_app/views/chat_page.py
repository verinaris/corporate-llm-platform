"""Chat-Seite mit Konversationsverlauf + optional RAG + Quellen-Details."""

import streamlit as st

from streamlit_app.api_client import APIClient, APIError
from streamlit_app.config import AVAILABLE_MODELS, DEFAULT_MODEL_LABEL


def render() -> None:
    st.title("💬 Chat")

    active_collection = st.session_state.get("active_collection")
    if active_collection and active_collection != "— keine —":
        st.success(
            f"📚 **RAG aktiv** — Antworten basieren auf der Sammlung "
            f"`{active_collection}` und enthalten Quellenangaben."
        )
    else:
        st.caption(
            "Tipp: Konversationen werden nur in diesem Browser-Tab gespeichert. "
            "Neuer Tab = neuer Chat. Sammlung in der Sidebar wählen für RAG."
        )

    _ensure_state()

    # Konversationsverlauf
    for idx, msg in enumerate(st.session_state["messages"]):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if sources := msg.get("sources"):
                _render_sources(sources, msg_idx=idx)
            if usage := msg.get("usage"):
                st.caption(_format_usage(usage))

    if prompt := st.chat_input("Was möchtest du wissen?"):
        _handle_user_message(prompt)


# ----------------------------------------------------------------------- #
# Helpers
# ----------------------------------------------------------------------- #

def _ensure_state() -> None:
    if "messages" not in st.session_state:
        st.session_state["messages"] = []


def _handle_user_message(prompt: str) -> None:
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    token = st.session_state.get("token")
    model_label = st.session_state.get("selected_model_label", DEFAULT_MODEL_LABEL)
    # Bevorzugt: id aus app.py (dynamisch geladen). Fallback: statisches Mapping.
    model_id = (
        st.session_state.get("selected_model_id")
        or AVAILABLE_MODELS.get(model_label)
    )

    active_collection = st.session_state.get("active_collection")
    use_rag = active_collection and active_collection != "— keine —"

    client = APIClient(token=token)
    api_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state["messages"]
    ]

    with st.chat_message("assistant"):
        spinner_text = (
            f"{model_label.split('·')[0].strip()} sucht in `{active_collection}`..."
            if use_rag
            else f"{model_label.split('·')[0].strip()} denkt nach..."
        )
        with st.spinner(spinner_text):
            try:
                response = client.chat(
                    messages=api_messages,
                    model=model_id,
                    collection=active_collection if use_rag else None,
                )
            except APIError as exc:
                st.error(f"Fehler: {exc.detail}")
                st.session_state["messages"].pop()
                return

        # Approval-Pending? -> Freundliche Info-Karte statt normale Antwort
        if response.get("_pending_approval"):
            request_id = response.get("request_id", "?")
            tool_name = response.get("tool_name", "?")
            st.info(
                f"⏳ **Freigabe erforderlich**\n\n"
                f"Der Vorgang fuer Tool **{tool_name}** wurde als "
                f"Antrag **Nr. {request_id}** eingereicht.\n\n"
                f"Ein Compliance-Officer wird die Freigabe pruefen. "
                f"Sie koennen den Status unter **Freigaben** verfolgen."
            )
            # Nachricht als Hinweis in History speichern und return
            st.session_state["messages"].append({
                "role": "assistant",
                "content": (
                    f"⏳ Antrag Nr. {request_id} fuer Tool '{tool_name}' "
                    f"wurde eingereicht. Warte auf Freigabe."
                ),
                "sources": [],
                "usage": {"input_tokens": 0, "output_tokens": 0, "model": "n/a"},
            })
            return

        st.markdown(response["content"])

        sources = response.get("sources", [])
        if sources:
            _render_sources(sources, msg_idx=len(st.session_state["messages"]))

        usage = response["usage"]
        st.caption(_format_usage({**usage, "model": response["model"]}))

    st.session_state["messages"].append(
        {
            "role": "assistant",
            "content": response["content"],
            "sources": sources,
            "usage": {**usage, "model": response["model"]},
        }
    )


def _render_sources(sources: list[dict], msg_idx: int = 0) -> None:
    """Quellen unter der Antwort als ausklappbare Cards mit Detail-Bereich."""
    if not sources:
        return

    with st.expander(f"📚 {len(sources)} Quelle(n) verwendet", expanded=False):
        for i, src in enumerate(sources, start=1):
            distance = src.get("distance", 1.0)
            # Relevanz-Score grob: 0=identisch → 100%, 1.5=irrelevant → 0%
            relevance_pct = max(0, min(100, int((1.5 - distance) / 1.5 * 100)))

            cols = st.columns([5, 1])
            cols[0].markdown(
                f"**{i}. {src['filename']}** · Seite {src['page']}"
            )
            cols[1].metric("Relevanz", f"{relevance_pct}%", label_visibility="collapsed")
            st.markdown(f"> _{src['excerpt']}_")

            # Detail-Bereich: voller Kontext + PDF-Download
            full_text = src.get("full_text") or ""
            doc_id = src.get("document_id", 0)
            key_base = f"src-{msg_idx}-{i}"

            sub_cols = st.columns([2, 2, 6])

            # Voller Chunk-Text als Expander (lazy)
            with sub_cols[0]:
                show_full = st.toggle(
                    "📖 Mehr Kontext",
                    key=f"{key_base}-full",
                    help="Den vollständigen Chunk anzeigen, aus dem die Antwort stammt",
                )

            # PDF-Download per Button (lazy fetch)
            with sub_cols[1]:
                if doc_id:
                    fetch_key = f"{key_base}-pdf-bytes"
                    if st.button(
                        "📥 PDF holen",
                        key=f"{key_base}-fetch-pdf",
                        help="Originaldatei vom Server abrufen",
                    ):
                        _fetch_pdf_into_state(doc_id, fetch_key, src["filename"])
                    if fetch_key in st.session_state:
                        st.download_button(
                            "💾 Speichern",
                            data=st.session_state[fetch_key]["bytes"],
                            file_name=st.session_state[fetch_key]["filename"],
                            mime="application/pdf",
                            key=f"{key_base}-download",
                        )

            if show_full and full_text:
                st.markdown("**Vollständiger Kontext:**")
                st.text_area(
                    "Chunk-Text",
                    value=full_text,
                    height=200,
                    key=f"{key_base}-fulltext-area",
                    label_visibility="collapsed",
                    disabled=True,
                )
            elif show_full and not full_text:
                st.info("Voller Kontext nicht verfügbar (älterer Chat-Eintrag).")

            st.divider()


def _fetch_pdf_into_state(document_id: int, state_key: str, filename: str) -> None:
    """Holt die PDF einmalig und legt sie in den Session-State."""
    token = st.session_state.get("token")
    client = APIClient(token=token)
    try:
        with st.spinner("Lade PDF…"):
            file_bytes, file_name = client.get_document_file(document_id)
        st.session_state[state_key] = {
            "bytes": file_bytes,
            "filename": file_name or filename,
        }
    except APIError as exc:
        st.error(f"PDF konnte nicht geladen werden: {exc.detail}")


def _format_usage(usage: dict) -> str:
    from streamlit_app.config import format_eur

    return (
        f"📊 {usage['total_tokens']} tokens "
        f"({usage['input_tokens']} in / {usage['output_tokens']} out)  ·  "
        f"💰 {format_eur(usage['cost_usd'], decimals=6)}  ·  "
        f"⏱ {usage['latency_ms']} ms  ·  "
        f"🤖 {usage.get('model', '?')}"
    )
