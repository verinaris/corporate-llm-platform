"""
👥 Benutzer — Streamlit-Page. Nur für Admins.

Zwei Tabs:
1. 📋 Übersicht — alle User der Instanz
2. ➕ Neu anlegen — Zugang für Demo-Interessenten oder Kollegen

Analogie: Wie die Gästeliste am Empfang. Wer draufsteht, kommt rein.
Eintragen kann sich niemand selbst — das macht nur der Admin.
"""

import secrets
import string

import streamlit as st

from streamlit_app.api_client import APIClient, APIError

# Rollen-Code -> Beschriftung im Dropdown (Werte aus app/models.py UserRole)
ROLLEN: dict[str, str] = {
    "user": "User — Standardzugang",
    "pharma-referent": "Pharma-Referent",
    "compliance-officer": "Compliance-Officer — sieht das Audit-Log",
    "qualified-reviewer": "Fachlicher Freigeber — gibt Automationen frei",
    "admin": "Admin — darf User verwalten",
}

PASSWORT_LAENGE = 16


def _neues_passwort(laenge: int = PASSWORT_LAENGE) -> str:
    """
    Zufallspasswort aus Buchstaben und Ziffern.

    secrets statt random: random ist bei bekanntem Startwert vorhersagbar,
    secrets nicht. Sonderzeichen bewusst weggelassen — das Passwort wird
    vorgelesen oder per Mail verschickt, da ist Verwechslungsfreiheit mehr
    wert als zwei Bit Entropie.
    """
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(laenge))


def render() -> None:
    st.title("👥 Benutzer")
    st.caption(
        "Zugänge anlegen und einsehen. Selbstregistrierung gibt es bewusst "
        "nicht — Zugänge vergibt ausschließlich der Admin."
    )

    user = st.session_state.get("user", {})
    if user.get("role") != "admin":
        st.error("Kein Zugriff. Diese Seite ist nur für Admins.")
        return

    client = APIClient(token=st.session_state.get("token"))

    tab_liste, tab_neu = st.tabs(["📋 Übersicht", "➕ Neu anlegen"])

    with tab_liste:
        _render_liste(client)

    with tab_neu:
        _render_neu(client)


def _render_liste(client: APIClient) -> None:
    try:
        users = client.list_users()
    except APIError as e:
        st.error(f"Konnte User nicht laden: {e.detail}")
        return

    if not users:
        st.info("Noch keine User angelegt.")
        return

    rows = [
        {
            "E-Mail": u.get("email") or "",
            "Rolle": u.get("role") or "",
            "Branche": u.get("branch") or "",
            "Aktiv": "✅" if u.get("is_active", u.get("active", True)) else "❌",
        }
        for u in users
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.caption(f"{len(users)} User insgesamt.")

    if st.button("🔄 Aktualisieren"):
        st.rerun()


def _render_neu(client: APIClient) -> None:
    # Branchen kommen aus dem Backend, nicht aus einer Liste in dieser Datei.
    # Neue Branche im Backend -> taucht hier automatisch auf.
    try:
        industries = client.list_industries()
    except APIError as e:
        st.error(f"Konnte Branchen nicht laden: {e.detail}")
        return

    branch_codes = [i["code"] for i in industries]
    branch_labels = [f"{i['icon']} {i['name']}" for i in industries]

    if "gen_passwort" not in st.session_state:
        st.session_state.gen_passwort = _neues_passwort()

    email = st.text_input("E-Mail", placeholder="interessent@kanzlei-beispiel.de")

    spalte_rolle, spalte_branche = st.columns(2)
    with spalte_rolle:
        rolle_label = st.selectbox("Rolle", list(ROLLEN.values()), index=0)
        rolle = next(k for k, v in ROLLEN.items() if v == rolle_label)
    with spalte_branche:
        branch_label = st.selectbox("Branche", branch_labels, index=0)
        branch = branch_codes[branch_labels.index(branch_label)]

    passwort = st.text_input(
        "Passwort",
        value=st.session_state.gen_passwort,
        help="Mindestens 8 Zeichen. Editierbar, falls du ein eigenes setzen willst.",
    )
    if st.button("🎲 Neues Passwort erzeugen"):
        st.session_state.gen_passwort = _neues_passwort()
        st.rerun()

    st.markdown("---")

    if st.button("➕ User anlegen", type="primary"):
        if not email.strip():
            st.warning("Bitte eine E-Mail angeben.")
            return
        if len(passwort) < 8:
            st.warning("Passwort muss mindestens 8 Zeichen haben.")
            return

        try:
            neu = client.create_user(
                email=email.strip(),
                password=passwort,
                role=rolle,
                branch=branch,
            )
        except APIError as e:
            if e.status_code == 409:
                st.error(f"{email.strip()} ist bereits vergeben.")
            else:
                st.error(f"Anlegen fehlgeschlagen: {e.detail}")
            return

        st.success(f"User {neu.get('email')} angelegt.")
        st.warning("Passwort jetzt notieren — gespeichert wird nur der Hash.")
        st.code(passwort, language=None)
        st.session_state.gen_passwort = _neues_passwort()
