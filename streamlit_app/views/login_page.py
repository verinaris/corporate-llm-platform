"""Login-Seite."""

import streamlit as st

from streamlit_app.api_client import APIClient, APIError
from streamlit_app.config import APP_ICON, APP_TITLE


def render() -> None:
    # Zentriertes Layout über Spalten
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown(
            f"<h1 style='text-align:center;'>{APP_ICON} {APP_TITLE}</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align:center; color:#888;'>Bitte anmelden, "
            "um fortzufahren.</p>",
            unsafe_allow_html=True,
        )
        st.write("")

        with st.form("login_form", clear_on_submit=False):
            email = st.text_input(
                "E-Mail",
                placeholder="dein.name@firma.de",
                autocomplete="username",
            )
            password = st.text_input(
                "Passwort",
                type="password",
                autocomplete="current-password",
            )
            submitted = st.form_submit_button(
                "Anmelden", use_container_width=True, type="primary"
            )

        if submitted:
            _handle_login(email, password)


def _handle_login(email: str, password: str) -> None:
    if not email or not password:
        st.warning("Bitte E-Mail und Passwort eingeben.")
        return

    client = APIClient()
    try:
        with st.spinner("Anmelden..."):
            result = client.login(email, password)
    except APIError as exc:
        if exc.status_code == 401:
            st.error("E-Mail oder Passwort ist falsch.")
        elif exc.status_code == 0:
            st.error(
                "Backend nicht erreichbar. Läuft uvicorn auf "
                "http://localhost:8000?"
            )
        else:
            st.error(f"Fehler: {exc.detail}")
        return

    st.session_state["token"] = result["access_token"]
    st.session_state["user"] = result["user"]
    st.rerun()
