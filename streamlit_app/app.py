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
from streamlit_app.passwords_util import neues_passwort
from streamlit_app.config import (
    APP_ICON,
    APP_TITLE,
    AVAILABLE_MODELS,
    DEFAULT_MODEL_LABEL,
)
from streamlit_app.views import (
    admin_page,
    businessplan_page,
    chat_page,
    compliance_page,
    documents_page,
    login_page,
    stats_page,
    users_page,
)
from streamlit_app.components.trial_banner import render_trial_banner
from streamlit_app.components.ai_disclosure_banner import (
    render_ai_disclosure_banner,
    _AI_DISCLOSURE_TEXT,
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
            "Verinaris — interne Plattform für KI-gestützte "
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
# KI-Transparenzhinweis (EU AI Act Art. 50) — fuer ALLE, auch vor Login.
# Der Trial-Banner wandert dagegen HINTER den Auth-Check: er ist jetzt
# user-spezifisch (Testphase pro User) und braucht den eingeloggten User.
# ----------------------------------------------------------------------- #
render_ai_disclosure_banner(
    already_acknowledged=bool(
        st.session_state.get("user", {}).get("ai_disclosure_ack_at")
    )
)


# ----------------------------------------------------------------------- #
# Auth-Check
# ----------------------------------------------------------------------- #

def _is_logged_in() -> bool:
    if "token" not in st.session_state:
        return False
    try:
        # /auth/me ist die Wahrheit ueber den User (inkl. branch) -- Ergebnis in
        # session_state uebernehmen, nicht verwerfen. Sonst fehlt der Navigation
        # die Branche und branchenabhaengige Reiter (z.B. Businessplan) greifen nicht.
        st.session_state["user"] = APIClient(token=st.session_state["token"]).me()
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

# --- KI-Transparenzhinweis, Variante A: blockierende Bestaetigung -------- #
# Wer den Hinweis noch nicht bestaetigt hat, muss das ZUERST tun (EU AI Act
# Art. 50, dokumentierte Kenntnisnahme). st.stop() blockiert die App, bis
# bestaetigt wurde. Nach der Bestaetigung entfaellt der dauerhafte Banner.
if user.get("ai_disclosure_ack_at") is None:
    st.markdown("## 🤖 Hinweis zur KI-Nutzung")
    st.warning(_AI_DISCLOSURE_TEXT)
    st.markdown(
        "Bitte bestätigen Sie, dass Sie diesen Hinweis zur Kenntnis "
        "genommen haben. Ohne Bestätigung können Sie die Anwendung "
        "nicht nutzen."
    )
    if st.button("✅ Verstanden — Hinweis zur Kenntnis genommen",
                 type="primary"):
        try:
            client = APIClient(token=st.session_state["token"])
            client.acknowledge_disclosure()
            st.session_state["user"] = client.me()  # Status auffrischen
            st.rerun()
        except APIError as exc:
            st.error(f"Bestätigung fehlgeschlagen: {exc.detail}")
    st.stop()

# Trial-Banner jetzt user-spezifisch (Variante B).
render_trial_banner()


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


def _fetch_industries() -> list[dict]:
    """Holt verfügbare Branchen-Profile vom Backend (cached pro Session)."""
    if "_industries_cache" in st.session_state:
        return st.session_state["_industries_cache"]
    try:
        industries = APIClient(token=st.session_state["token"]).list_industries()
    except APIError:
        industries = [{
            "code": "generic", "name": "Generisch", "short_name": "Generic",
            "icon": "🌐", "description": "", "is_default": True,
        }]
    st.session_state["_industries_cache"] = industries
    return industries


def _render_branch_selector(user: dict) -> None:
    """
    Branchen-Profil-Wähler in der Sidebar.

    User wählt einmal — Plattform passt sich überall an (Chat-Plugin,
    Businessplan-Vorlagen, Industry-Checks).
    """
    industries = _fetch_industries()
    current_branch = user.get("branch", "generic")

    # Code → Index für selectbox
    codes = [i["code"] for i in industries]
    labels = [f"{i['icon']} {i['name']}" for i in industries]
    current_idx = codes.index(current_branch) if current_branch in codes else 0

    st.markdown("**🏢 Mein Branchen-Profil**")

    # Ist die AKTUELLE Branche selbst waehlbar? Wenn nicht (z.B. Pharma), darf
    # der User sie nicht selbst wechseln -- das Backend lehnt es ohnehin ab.
    # Statt eines Dropdowns, das bei jedem Klick "nein" sagt, ein klarer Hinweis.
    current_profile = next(
        (i for i in industries if i["code"] == current_branch), None
    )
    current_self_assignable = (
        current_profile.get("self_assignable", True) if current_profile else True
    )

    is_admin = user.get("role") == "admin"
    if not current_self_assignable and not is_admin:
        label = current_profile["name"] if current_profile else current_branch
        icon = current_profile["icon"] if current_profile else "🏢"
        st.info(
            f"{icon} **{label}**\n\n"
            "Diese Branche ist reguliert und kann nur von einem Admin "
            "geändert werden."
        )
    else:
        chosen_label = st.selectbox(
            "Branche",
            labels,
            index=current_idx,
            label_visibility="collapsed",
            help=(
                "Steuert das Pharma-Plugin im Chat, die Vorlagen im Businessplan-"
                "Generator und (später) verfügbare Agenten."
            ),
        )
        chosen_code = codes[labels.index(chosen_label)]

        # Wenn geändert: an Backend senden + lokalen User-State aktualisieren
        if chosen_code != current_branch:
            try:
                client = APIClient(token=st.session_state["token"])
                updated = client.update_my_branch(chosen_code)
                # User-State im Frontend mitziehen
                st.session_state["user"]["branch"] = updated["branch"]
                # Caches platt machen, die branchen-abhängig sind
                st.session_state.pop("_bp_templates_cache", None)
                st.success(
                    f"Branche gewechselt zu: {updated['branch_profile']['name']}"
                )
                st.rerun()
            except APIError as exc:
                st.error(f"Branche konnte nicht gewechselt werden: {exc.detail}")

    # Aktive Branche → Compliance-Hinweis
    if current_branch == "pharma":
        st.info(
            "💊 **Pharma-Mode aktiv**\n\n"
            "Chat folgt HWG/AMG-Regeln. Antworten enthalten einen "
            "Compliance-Hinweis. Cloud-Modelle sind gesperrt.",
            icon="⚖️",
        )


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

    # --- Branchen-Profil-Wähler ---
    _render_branch_selector(user)

    st.markdown("---")

    # Navigation. Zwei getrennte Rechte, gespiegelt aus app/auth/permissions.py:
    #   - darf_audit: das DSGVO-Audit-Log sehen (admin, compliance-officer)
    #   - darf_freigeben: Freigaben + Wissensbibliothek (zusaetzlich qualified-reviewer)
    # Der qualified-reviewer soll hochladen und freigeben koennen, aber NICHT
    # ins Audit-Log schauen -- deshalb duerfen die beiden nicht an derselben
    # Bedingung haengen.
    rolle = user["role"]
    darf_audit = rolle in ("admin", "compliance-officer")
    darf_freigeben = rolle in ("admin", "compliance-officer", "qualified-reviewer")
    branche = user.get("branch", "generic")

    nav_options = ["💬 Chat", "📈 Verbrauch", "✅ Freigaben"]

    # Businessplan ist ein branchenspezifisches Tool -- fuer Pharma nicht sinnvoll.
    if branche != "pharma":
        nav_options.insert(1, "📊 Businessplan")

    # Wissensbibliothek: wer freigeben darf, darf auch Dokumente pflegen.
    if darf_freigeben:
        nav_options.insert(1, "📚 Wissensbibliothek")

    # Audit-Log strikt nur fuer Audit-Berechtigte -- NICHT qualified-reviewer.
    if darf_audit:
        nav_options.append("🛡️ Admin / Compliance")

    if rolle == "admin":
        nav_options.append("👥 Benutzer")
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
            "Wählen Sie eine Sammlung, um Antworten aus Ihren Dokumenten zu erhalten "
            "(RAG). Bei 'keine' antwortet Claude aus Allgemeinwissen."
        ),
    )
    st.session_state["active_collection"] = selected_collection

    # Nur wenn eine echte Sammlung gewaehlt ist, ist die Anzahl der Textstellen
    # (top_k) relevant -- ohne RAG sucht das Modell nicht in Dokumenten.
    if selected_collection and selected_collection != "— keine —":
        st.session_state["rag_top_k"] = st.slider(
            "Textstellen durchsuchen",
            min_value=4,
            max_value=10,
            value=st.session_state.get("rag_top_k", 6),
            help=(
                "Wie viele Textstellen aus der Wissensbibliothek für die Antwort "
                "herangezogen werden. Mehr = gruendlicher, aber langsamer. Bei sehr "
                "vielen kann die Antwort auch abgeschnitten werden."
            ),
        )

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
                "💻 Lokale Modelle (Ollama) = laufen auf diesem Server, "
                "0$ pro Token, aber langsamer und meist schwächer."
            ),
        )
        # Banner unter dem Selector wenn lokales Modell
        selected_id = model_dict[selected]
        if any(selected_id.lower().startswith(p) for p in (
            "llama", "qwen", "mistral", "phi", "gemma"
        )) or ":" in selected_id:
            st.caption("💻 **Lokales Modell** — Ihre Daten verlassen diese Installation nicht")

    st.session_state["selected_model_label"] = selected
    st.session_state["selected_model_id"] = model_dict.get(selected) if model_dict else None

    if st.button("🔄 Modelle aktualisieren", use_container_width=True):
        st.session_state.pop("_models_cache", None)
        st.rerun()

    st.markdown("---")

    with st.expander("🔑 Passwort ändern"):
        if st.button("🎲 Sicheres Passwort vorschlagen", use_container_width=True,
                     key="_pw_gen_btn"):
            st.session_state["pw_vorschlag"] = neues_passwort()

        if st.session_state.get("pw_vorschlag"):
            st.code(st.session_state["pw_vorschlag"], language=None)
            st.caption(
                "⚠️ Bitte JETZT notieren — nach dem Ändern wird das Passwort "
                "nicht mehr angezeigt. Tragen Sie es unten als neues Passwort ein."
            )

        with st.form("pw_change_form", clear_on_submit=False):
            _pw_alt = st.text_input("Aktuelles Passwort", type="password", key="_pw_alt")
            _pw_neu = st.text_input("Neues Passwort", type="password", key="_pw_neu")
            _pw_neu2 = st.text_input("Neues Passwort wiederholen", type="password", key="_pw_neu2")
            _pw_submit = st.form_submit_button("Passwort ändern", use_container_width=True)

        if _pw_submit:
            if not _pw_alt or not _pw_neu:
                st.warning("Bitte alle Felder ausfüllen.")
            elif _pw_neu != _pw_neu2:
                st.warning("Die beiden neuen Passwörter stimmen nicht überein.")
            elif len(_pw_neu) < 8:
                st.warning("Das neue Passwort muss mindestens 8 Zeichen lang sein.")
            elif _pw_neu == _pw_alt:
                st.warning("Das neue Passwort muss sich vom alten unterscheiden.")
            else:
                try:
                    client = APIClient(token=st.session_state["token"])
                    client.change_password(_pw_alt, _pw_neu)
                    st.session_state.pop("pw_vorschlag", None)
                    st.success("Passwort geändert. Bitte beim nächsten Login das neue verwenden.")
                except APIError as exc:
                    st.error(f"Änderung fehlgeschlagen: {exc.detail}")

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
elif page_label == "📊 Businessplan":
    businessplan_page.render()
elif page_label == "📈 Verbrauch":
    stats_page.render()
elif page_label == "✅ Freigaben":
    compliance_page.render()
elif page_label == "🛡️ Admin / Compliance":
    admin_page.render()
elif page_label == "👥 Benutzer":
    users_page.render()
