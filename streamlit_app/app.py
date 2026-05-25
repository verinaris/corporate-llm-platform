"""
Streamlit-Haupt-App.

Startet mit:
    streamlit run streamlit_app/app.py

Standardmäßig auf http://localhost:8501.
Wichtig: Das FastAPI-Backend MUSS parallel laufen
(uvicorn app.main:app --reload  →  http://localhost:8000).
"""

# --- Projekt-Root zum Python-Path (muss VOR allen lokalen Imports stehen!) ---
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
# ---------------------------------------------------------------------------

import streamlit as st

from streamlit_app.api_client import APIClient, APIError
from streamlit_app.config import (
    APP_ICON,
    APP_TITLE,
    AVAILABLE_MODELS,
    DEFAULT_MODEL_LABEL,
)
from streamlit_app.views import chat_page, login_page, stats_page


# ----------------------------------------------------------------------- #
# Seiten-Setup
# ----------------------------------------------------------------------- #

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": (
            "Corporate LLM Platform — interne Plattform für KI-gestützte "
            "Wissensarbeit. Konzipiert mit DSGVO und EU AI Act im Blick."
        ),
    },
)

# Sprachattribut auf "de" setzen (Streamlit setzt sonst "en")
# und Basis-Style für besseren Fokus-Ring (WCAG 2.4.7 Focus Visible)
st.markdown(
    """
    <script>
    document.documentElement.lang = "de";
    </script>
    <style>
      *:focus-visible {
        outline: 3px solid #0066CC !important;
        outline-offset: 2px !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------- #
# Auth-Check
# ----------------------------------------------------------------------- #

def _is_logged_in() -> bool:
    if "token" not in st.session_state:
        return False
    try:
        APIClient(token=st.session_state["token"]).me()
        return True
    except APIError:
        for key in ("token", "user", "messages"):
            st.session_state.pop(key, None)
        return False


if not _is_logged_in():
    login_page.render()
    st.stop()


# ----------------------------------------------------------------------- #
# Sidebar
# ----------------------------------------------------------------------- #

user = st.session_state["user"]

with st.sidebar:
    st.markdown(f"### {APP_ICON} {APP_TITLE}")
    st.markdown("---")

    st.markdown(f"**👤 {user['email']}**")
    role_emoji = {
        "admin": "🛡",
        "compliance-officer": "📋",
        "pharma-referent": "💊",
        "user": "👤",
    }.get(user["role"], "👤")
    st.caption(f"{role_emoji} Rolle: `{user['role']}`")
    st.caption(f"🏢 Branche: `{user['branch']}`")

    # Branchen-Hinweis: Wenn Pharma → Compliance-Banner
    if user["branch"] == "pharma":
        st.info(
            "💊 **Pharma-Mode aktiv**\n\n"
            "Antworten folgen HWG/AMG-Regeln. Jede Antwort enthält einen "
            "Compliance-Hinweis am Ende.",
            icon="⚖️",
        )

    st.markdown("---")

    page_label = st.radio(
        "Navigation",
        ["💬 Chat", "📊 Verbrauch"],
        label_visibility="collapsed",
    )

    st.markdown("---")

    st.markdown("**🤖 Modell**")
    selected = st.selectbox(
        "Modell",
        list(AVAILABLE_MODELS.keys()),
        index=list(AVAILABLE_MODELS.keys()).index(
            st.session_state.get("selected_model_label", DEFAULT_MODEL_LABEL)
        ),
        label_visibility="collapsed",
    )
    st.session_state["selected_model_label"] = selected

    st.markdown("---")

    if st.button("🗑️ Verlauf löschen", use_container_width=True):
        st.session_state["messages"] = []
        st.rerun()

    if st.button("🚪 Logout", use_container_width=True):
        for key in ("token", "user", "messages"):
            st.session_state.pop(key, None)
        st.rerun()


# ----------------------------------------------------------------------- #
# Page-Routing
# ----------------------------------------------------------------------- #

if page_label == "💬 Chat":
    chat_page.render()
elif page_label == "📊 Verbrauch":
    stats_page.render()
