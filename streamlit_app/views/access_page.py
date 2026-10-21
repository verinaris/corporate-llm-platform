"""
🔐 Zugriffsrechte — Streamlit-Page. Nur für Admins. (Mandantentrennung, E5)

Wer darf welche Sammlung lesen oder pflegen? Die Seite zeigt ausschließlich
Metadaten (Namen, Besitzer, Mitglieder), nie Inhalte.

Analogie: das Schlüsselbuch am Empfang. Der Empfang trägt ein, wer welchen
Raum betreten darf, geht aber selbst nicht hinein.
"""

import streamlit as st

from streamlit_app.api_client import APIClient, APIError

STUFEN: dict[str, str] = {
    "read": "Lesen",
    "maintain": "Pflegen (hochladen, ändern, löschen)",
}


def _do(action, erfolg: str) -> None:
    """Aktion ausführen, Meldung für den nächsten Lauf merken, neu laden."""
    try:
        action()
    except APIError as e:
        st.error(f"Fehlgeschlagen: {e}")
        return
    st.session_state["access_msg"] = erfolg
    st.rerun()


def render() -> None:
    st.title("🔐 Zugriffsrechte")
    st.caption(
        "Wer darf welche Sammlung lesen oder pflegen? Sie sehen hier nur Namen und "
        "Rechte, keine Inhalte. Tragen Sie sich selbst als Mitglied ein, wird das "
        "als Notfallzugriff protokolliert."
    )

    me = st.session_state.get("user", {})
    if me.get("role") != "admin":
        st.error("Kein Zugriff. Diese Seite ist nur für Admins.")
        return

    if "access_msg" in st.session_state:
        st.success(st.session_state.pop("access_msg"))

    client = APIClient(token=st.session_state.get("token"))
    try:
        colls = client.list_collection_access()
        users = client.list_users()
    except APIError as e:
        st.error(f"Daten konnten nicht geladen werden: {e}")
        return

    if not colls:
        st.info("Noch keine Sammlungen vorhanden.")
        return

    aktive = sorted(u["email"] for u in users if u.get("is_active"))

    # ---------------- Übersicht ----------------
    verwaist = [c["name"] for c in colls if not c["owner_active"]]
    if verwaist:
        st.warning(
            f"{len(verwaist)} Sammlung(en) sind verwaist (Besitzer inaktiv): "
            + ", ".join(verwaist)
            + ". Übertragen Sie den Besitz, sonst kommt niemand mehr an die Inhalte."
        )

    st.dataframe(
        [
            {
                "Sammlung": c["name"],
                "Besitzer": c["owner"] + ("" if c["owner_active"] else "  ⚠️ inaktiv"),
                "Für alle lesbar": "ja" if c["open_for_all"] else "nein",
                "Mitglieder": len(c["members"]),
            }
            for c in colls
        ],
        use_container_width=True,
        hide_index=True,
    )

    # ---------------- Eine Sammlung bearbeiten ----------------
    st.markdown("---")
    wahl = st.selectbox("Sammlung bearbeiten", [c["name"] for c in colls])
    c = next(x for x in colls if x["name"] == wahl)

    st.markdown(
        f"**Besitzer:** {c['owner']}"
        + ("" if c["owner_active"] else "  ⚠️ inaktiv, die Sammlung ist verwaist")
    )

    st.markdown("**Mitglieder**")
    if c["members"]:
        for m in c["members"]:
            col1, col2, col3 = st.columns([3, 3, 1])
            col1.write(m["email"])
            col2.write(STUFEN.get(m["level"], m["level"]))
            if col3.button("Entfernen", key=f"rm-{wahl}-{m['email']}"):
                _do(
                    lambda: client.revoke_collection_member(wahl, m["email"]),
                    f"Recht von {m['email']} an '{wahl}' entzogen.",
                )
    else:
        st.caption("Keine Mitglieder eingetragen.")

    BITTE = "— bitte wählen —"
    kandidaten = [e for e in aktive if e.lower() != c["owner"].lower()]
    auswahl = [BITTE] + kandidaten

    with st.form(f"add-{wahl}", clear_on_submit=True):
        st.markdown("**Mitglied eintragen oder Stufe ändern**")
        email = st.selectbox("User", auswahl, key=f"add-user-{wahl}")
        st.caption(f"{len(kandidaten)} aktive User zur Auswahl")
        email = None if email == BITTE else email
        stufe = st.radio("Stufe", list(STUFEN), format_func=STUFEN.get,
                         horizontal=True, key=f"add-level-{wahl}")
        if email and email.lower() == (me.get("email") or "").lower():
            st.caption("⚠️ Das sind Sie selbst: wird als Notfallzugriff protokolliert.")
        if st.form_submit_button("Eintragen") and email:
            _do(
                lambda: client.grant_collection_member(wahl, email, stufe),
                f"{email} hat jetzt '{STUFEN[stufe]}' für '{wahl}'.",
            )

    with st.form(f"vis-{wahl}"):
        st.markdown("**Sichtbarkeit**")
        offen = st.checkbox(
            "Für alle angemeldeten User lesbar (z. B. öffentliche Regulierungstexte)",
            value=c["open_for_all"],
            key=f"vis-box-{wahl}",
        )
        st.caption("Nie für Mandantenakten oder personenbezogene Inhalte verwenden.")
        if st.form_submit_button("Sichtbarkeit übernehmen") and offen != c["open_for_all"]:
            _do(
                lambda: client.set_collection_visibility(wahl, offen),
                f"'{wahl}' ist jetzt " + ("für alle lesbar." if offen else "wieder geschlossen."),
            )

    with st.form(f"owner-{wahl}"):
        st.markdown("**Besitz übertragen**")
        neu = st.selectbox("Neuer Besitzer", auswahl, key=f"owner-user-{wahl}")
        neu = None if neu == BITTE else neu
        st.caption(
            "Der bisherige Besitzer verliert den Zugriff, sofern Sie ihn nicht "
            "anschließend als Mitglied eintragen."
        )
        bestaetigt = st.checkbox("Ich will den Besitz wirklich übertragen", key=f"owner-ok-{wahl}")
        if st.form_submit_button("Übertragen"):
            if not bestaetigt:
                st.error("Bitte zuerst bestätigen.")
            elif neu:
                _do(
                    lambda: client.transfer_collection_owner(wahl, neu),
                    f"'{wahl}' gehört jetzt {neu}.",
                )
