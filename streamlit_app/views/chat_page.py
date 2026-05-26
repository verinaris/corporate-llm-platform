"""Chat-Seite mit Konversationsverlauf + optional RAG."""

import streamlit as st

from streamlit_app.api_client import APIClient, APIError
from streamlit_app.config import AVAILABLE_MODELS, DEFAULT_MODEL_LABEL


def render() -> None:
    st.title("💬 Chat")

    # Banner wenn RAG aktiv
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
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if sources := msg.get("sources"):
                _render_sources(sources)
            if usage := msg.get("usage"):
                st.caption(_format_usage(usage))

    # Eingabe
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
    model_id = AVAILABLE_MODELS.get(model_label)

    # RAG-Parameter
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

        st.markdown(response["content"])

        sources = response.get("sources", [])
        if sources:
            _render_sources(sources)

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


def _render_sources(sources: list[dict]) -> None:
    """Quellen unter der Antwort als ausklappbare Cards."""
    if not sources:
        return
    with st.expander(f"📚 {len(sources)} Quelle(n) verwendet", expanded=False):
        for i, src in enumerate(sources, start=1):
            # ChromaDB-Distance: 0=identisch, ~1.5=irrelevant
            # Relevanz-Score grob 1.0 → 100%, 1.5 → 25%
            distance = src.get("distance", 1.0)
            relevance_pct = max(0, min(100, int((1.5 - distance) / 1.5 * 100)))

            cols = st.columns([5, 1])
            cols[0].markdown(
                f"**{i}. {src['filename']}** · Seite {src['page']}"
            )
            cols[1].metric("Relevanz", f"{relevance_pct}%", label_visibility="collapsed")
            st.markdown(f"> _{src['excerpt']}_")
            st.divider()


def _format_usage(usage: dict) -> str:
    cost_eur_approx = usage["cost_usd"] * 0.92
    return (
        f"📊 {usage['total_tokens']} tokens "
        f"({usage['input_tokens']} in / {usage['output_tokens']} out)  ·  "
        f"💰 ${usage['cost_usd']:.6f} (~{cost_eur_approx:.4f} €)  ·  "
        f"⏱ {usage['latency_ms']} ms  ·  "
        f"🤖 {usage.get('model', '?')}"
    )
