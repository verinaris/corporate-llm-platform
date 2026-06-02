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
from streamlit_app.views import (
    chat_page,
    documents_page,
    login_page,
    stats_page,
)


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


def _fetch_collections() -> list[str]:
    """Holt die Liste der Sammlungen vom Backend (cached pro Session)."""
    if "_collections_cache" in st.session_state:
        return st.session_state["_collections_cache"]
    try:
        collections = APIClient(token=st.session_state["token"]).list_collections()
        names = ["— keine —"] + [c["name"] for c in collections]
    except APIError:
        names = ["— keine —"]
    st.session_state["_collections_cache"] = names
    return names


def _fetch_models() -> dict[str, str]:
    """
    Holt die verfügbaren Modelle vom Backend (cached pro Session).

    Liefert ein Dict {label: model_id}, sortiert: erst Cloud (Anthropic),
    dann lokale (Ollama).
    """
    if "_models_cache" in st.session_state:
        return st.session_state["_models_cache"]

    try:
        data = APIClient(token=st.session_state["token"]).list_available_models()
    except APIError:
        # Backend down? → Fallback auf statisches Mapping
        st.session_state["_models_cache"] = dict(AVAILABLE_MODELS)
        return st.session_state["_models_cache"]

    result: dict[str, str] = {}
    for provider in data.get("providers", []):
        if not provider.get("available"):
            continue
        for m in provider.get("models", []):
            label = m.get("label") or m.get("id")
            result[label] = m["id"]

    if not result:
        result = dict(AVAILABLE_MODELS)

    st.session_state["_models_cache"] = result
    return result


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

    if user["branch"] == "pharma":
        st.info(
            "💊 **Pharma-Mode aktiv**\n\n"
            "Antworten folgen HWG/AMG-Regeln. Jede Antwort enthält einen "
            "Compliance-Hinweis am Ende.",
            icon="⚖️",
        )

    st.markdown("---")

    # Navigation — Documents-Page nur für Admin/Compliance-Officer
    nav_options = ["💬 Chat", "📊 Verbrauch"]
    if user["role"] in ("admin", "compliance-officer"):
        nav_options.insert(1, "📚 Wissensbibliothek")
    page_label = st.radio(
        "Navigation",
        nav_options,
        label_visibility="collapsed",
    )

    st.markdown("---")

    # RAG-Sammlung wählen
    st.markdown("**📚 Wissensbibliothek**")
    collections = _fetch_collections()
    selected_collection = st.selectbox(
        "Sammlung",
        collections,
        index=collections.index(
            st.session_state.get("active_collection", "— keine —")
        ) if st.session_state.get("active_collection", "— keine —") in collections else 0,
        label_visibility="collapsed",
        help=(
            "Wähle eine Sammlung, um Antworten aus deinen Dokumenten zu erhalten "
            "(RAG). Bei 'keine' antwortet Claude aus Allgemeinwissen."
        ),
    )
    st.session_state["active_collection"] = selected_collection

    if st.button("🔄 Sammlungen aktualisieren", use_container_width=True):
        st.session_state.pop("_collections_cache", None)
        st.rerun()

    st.markdown("---")

    st.markdown("**🤖 Modell**")
    model_dict = _fetch_models()  # label -> model_id

    if not model_dict:
        st.warning("Keine Modelle verfügbar (Backend nicht erreichbar?)")
        selected = DEFAULT_MODEL_LABEL
    else:
        # Default-Index ermitteln
        labels = list(model_dict.keys())
        prev_label = st.session_state.get("selected_model_label")
        if prev_label in labels:
            default_idx = labels.index(prev_label)
        else:
            # Sonnet 4.6 als Default, fallback auf 0
            default_idx = next(
                (i for i, lbl in enumerate(labels) if "Sonnet 4.6" in lbl),
                0,
            )
        selected = st.selectbox(
            "Modell",
            labels,
            index=default_idx,
            label_visibility="collapsed",
            help=(
                "☁️ Cloud-Modelle = Claude (kosten pro Token).\n"
                "💻 Lokale Modelle (Ollama) = laufen auf deinem Mac, "
                "0$ pro Token, aber langsamer und meist schwächer."
            ),
        )
        # Banner unter dem Selector wenn lokales Modell
        selected_id = model_dict[selected]
        if any(selected_id.lower().startswith(p) for p in (
            "llama", "qwen", "mistral", "phi", "gemma"
        )) or ":" in selected_id:
            st.caption("💻 **Lokales Modell** — keine Daten verlassen deinen Mac")

    st.session_state["selected_model_label"] = selected
    st.session_state["selected_model_id"] = model_dict.get(selected) if model_dict else None

    if st.button("🔄 Modelle aktualisieren", use_container_width=True):
        st.session_state.pop("_models_cache", None)
        st.rerun()

    st.markdown("---")

    if st.button("🗑️ Verlauf löschen", use_container_width=True):
        st.session_state["messages"] = []
        st.rerun()

    if st.button("🚪 Logout", use_container_width=True):
        for key in ("token", "user", "messages", "_collections_cache", "_models_cache"):
            st.session_state.pop(key, None)
        st.rerun()


# ----------------------------------------------------------------------- #
# Page-Routing
# ----------------------------------------------------------------------- #

if page_label == "💬 Chat":
    chat_page.render()
elif page_label == "📚 Wissensbibliothek":
    documents_page.render()
elif page_label == "📊 Verbrauch":
    stats_page.render()
