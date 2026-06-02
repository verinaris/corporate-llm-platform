"""Stats-Seite — eigene Token-/Kosten-Auswertung (Anzeige in EUR)."""

import streamlit as st

from streamlit_app.api_client import APIClient, APIError
from streamlit_app.config import format_eur, usd_to_eur


def render() -> None:
    st.title("📊 Verbrauch")

    user = st.session_state.get("user", {})
    if user.get("role") == "admin":
        st.caption("Du bist Admin → du siehst Verbrauch aller User.")
    else:
        st.caption("Du siehst nur deine eigenen Verbräuche.")

    token = st.session_state.get("token")
    client = APIClient(token=token)

    try:
        stats = client.stats()
    except APIError as exc:
        st.error(f"Stats konnten nicht geladen werden: {exc.detail}")
        return

    # Top-Kacheln
    cols = st.columns(4)
    cols[0].metric("Requests", stats["total_requests"])
    cols[1].metric("Input-Tokens", f"{stats['total_input_tokens']:,}".replace(",", "."))
    cols[2].metric("Output-Tokens", f"{stats['total_output_tokens']:,}".replace(",", "."))
    cols[3].metric("Kosten", format_eur(stats["total_cost_usd"], decimals=4))

    # Dezenter Hinweis zum Wechselkurs
    st.caption(
        "💱 Kosten umgerechnet aus USD (Anthropic-Abrechnung). "
        "Lokale Modelle (Ollama) = kostenlos. "
        "Wechselkurs in `streamlit_app/config.py` anpassbar."
    )

    st.divider()

    # Aufschlüsselung nach Modell
    if stats["by_model"]:
        st.subheader("Pro Modell")
        rows = []
        for model, m in stats["by_model"].items():
            rows.append(
                {
                    "Modell": model,
                    "Requests": m["requests"],
                    "Input-Tokens": m["input_tokens"],
                    "Output-Tokens": m["output_tokens"],
                    "Kosten (EUR)": round(usd_to_eur(m["cost_usd"]), 6),
                }
            )
        st.dataframe(rows, use_container_width=True, hide_index=True)

    # Aufschlüsselung nach User (nur Admin sieht mehr als sich selbst)
    if stats["by_user"]:
        st.subheader("Pro User")
        rows = []
        for user_email, u in stats["by_user"].items():
            rows.append(
                {
                    "User": user_email,
                    "Requests": u["requests"],
                    "Tokens gesamt": u["total_tokens"],
                    "Kosten (EUR)": round(usd_to_eur(u["cost_usd"]), 6),
                }
            )
        st.dataframe(rows, use_container_width=True, hide_index=True)

    if st.button("🔄 Aktualisieren"):
        st.rerun()
