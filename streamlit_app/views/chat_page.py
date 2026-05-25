"""Chat-Seite mit Konversationsverlauf."""

import streamlit as st

from streamlit_app.api_client import APIClient, APIError
from streamlit_app.config import AVAILABLE_MODELS, DEFAULT_MODEL_LABEL


def render() -> None:
    st.title("💬 Chat")
    st.caption(
        "Tipp: Konversationen werden nur in diesem Browser-Tab gespeichert. "
        "Neuer Tab = neuer Chat."
    )

    _ensure_state()

    # Konversationsverlauf anzeigen
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
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
    # User-Message anhängen + sofort anzeigen
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # API-Aufruf
    token = st.session_state.get("token")
    model_label = st.session_state.get("selected_model_label", DEFAULT_MODEL_LABEL)
    model_id = AVAILABLE_MODELS.get(model_label)
    client = APIClient(token=token)

    # Messages an Backend (ohne usage-Feld!)
    api_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state["messages"]
    ]

    with st.chat_message("assistant"):
        with st.spinner(f"{model_label.split('·')[0].strip()} denkt nach..."):
            try:
                response = client.chat(messages=api_messages, model=model_id)
            except APIError as exc:
                st.error(f"Fehler: {exc.detail}")
                # User-Message wieder zurücknehmen, damit kein "halber" Verlauf
                st.session_state["messages"].pop()
                return

        st.markdown(response["content"])
        usage = response["usage"]
        st.caption(_format_usage({**usage, "model": response["model"]}))

    st.session_state["messages"].append(
        {
            "role": "assistant",
            "content": response["content"],
            "usage": {**usage, "model": response["model"]},
        }
    )


def _format_usage(usage: dict) -> str:
    cost_eur_approx = usage["cost_usd"] * 0.92  # grobe USD→EUR-Schätzung
    return (
        f"📊 {usage['total_tokens']} tokens "
        f"({usage['input_tokens']} in / {usage['output_tokens']} out)  ·  "
        f"💰 ${usage['cost_usd']:.6f} (~{cost_eur_approx:.4f} €)  ·  "
        f"⏱ {usage['latency_ms']} ms  ·  "
        f"🤖 {usage.get('model', '?')}"
    )
