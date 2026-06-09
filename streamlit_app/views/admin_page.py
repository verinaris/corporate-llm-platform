"""
🛡️ Admin / Compliance — Streamlit-Page.

Drei Tabs:
1. 📜 Audit-Log — Filter + Anzeige (Admin + Compliance-Officer)
2. 🗑 DSGVO Art. 17 — User vollständig löschen (nur Admin)
3. 📥 DSGVO Art. 15 — Datenexport für User (nur Admin)
"""

import json

import streamlit as st

from streamlit_app.api_client import APIClient, APIError


def render() -> None:
    st.title("🛡️ Admin / Compliance")
    st.caption(
        "Audit-Trail und DSGVO-Funktionen. "
        "Nur Admin und Compliance-Officer haben Zugriff."
    )

    user = st.session_state.get("user", {})
    if user.get("role") not in ("admin", "compliance-officer"):
        st.error("Kein Zugriff. Diese Seite ist nur für Admin/Compliance-Officer.")
        return

    token = st.session_state.get("token")
    client = APIClient(token=token)

    is_admin = user.get("role") == "admin"

    if is_admin:
        tab_audit, tab_delete, tab_export = st.tabs(
            ["📜 Audit-Log", "🗑 DSGVO Art. 17 — Löschen", "📥 DSGVO Art. 15 — Export"]
        )
    else:
        # Compliance-Officer: nur Audit-Log
        (tab_audit,) = st.tabs(["📜 Audit-Log"])

    with tab_audit:
        _render_audit_log(client)

    if is_admin:
        with tab_delete:
            _render_dsgvo_delete(client)
        with tab_export:
            _render_dsgvo_export(client)


# ----------------------------------------------------------------------- #
# Audit-Log
# ----------------------------------------------------------------------- #

def _render_audit_log(client: APIClient) -> None:
    st.subheader("📜 Audit-Log durchsuchen")

    # Filter
    col1, col2, col3 = st.columns(3)

    with col1:
        filter_email = st.text_input(
            "User-E-Mail (Filter)",
            placeholder="z.B. admin@example.com",
            help="Leer = alle User",
        )

    with col2:
        try:
            actions = ["(alle)"] + client.list_audit_actions()
        except APIError as exc:
            st.error(f"Aktionen konnten nicht geladen werden: {exc.detail}")
            return
        filter_action = st.selectbox("Aktion", actions, index=0)

    with col3:
        limit = st.number_input("Max. Ergebnisse", min_value=10, max_value=1000, value=100, step=50)

    # Laden
    try:
        entries = client.list_audit_log(
            user_email=filter_email or None,
            action=None if filter_action == "(alle)" else filter_action,
            limit=int(limit),
        )
    except APIError as exc:
        st.error(f"Audit-Log konnte nicht geladen werden: {exc.detail}")
        return

    if not entries:
        st.info("Keine Einträge gefunden (für diesen Filter).")
        return

    st.caption(f"**{len(entries)} Einträge** (neueste zuerst)")

    # Tabelle
    rows = []
    for e in entries:
        icon = "✅" if e["success"] else "❌"
        details_short = ""
        if e.get("details"):
            try:
                d = json.loads(e["details"])
                details_short = ", ".join(f"{k}={v}" for k, v in list(d.items())[:3])
            except (json.JSONDecodeError, TypeError):
                details_short = str(e["details"])[:80]

        rows.append({
            "Zeitpunkt": e["timestamp"][:19].replace("T", " "),
            "User": e["user_email"],
            "Rolle": e["user_role"],
            "Aktion": f"{icon} {e['action']}",
            "Ziel": f"{e.get('target_type') or ''} {e.get('target_id') or ''}".strip(),
            "Details": details_short,
            "IP": e.get("ip_address") or "",
        })

    st.dataframe(rows, use_container_width=True, hide_index=True)


# ----------------------------------------------------------------------- #
# DSGVO Art. 17 — User-Löschung
# ----------------------------------------------------------------------- #

def _render_dsgvo_delete(client: APIClient) -> None:
    st.subheader("🗑 DSGVO Art. 17 — Recht auf Vergessenwerden")

    st.warning(
        "**Achtung — irreversibel:**\n\n"
        "Diese Aktion löscht User-PII (E-Mail, Passwort), alle Dokumente und "
        "Businesspläne dieses Users. Token-Logs und Audit-Trail bleiben "
        "**pseudonymisiert** (gesetzliche Aufbewahrungspflicht).\n\n"
        "Der User-Datensatz bleibt mit Pseudonym `deleted_user_<id>` bestehen — "
        "Foreign-Keys werden nicht verwaist.",
        icon="⚠️",
    )

    user_id = st.number_input(
        "User-ID zum Löschen",
        min_value=1, step=1,
        help="Die User-ID findest du im Audit-Log oder via User-Verwaltung.",
    )

    expected = f"DELETE USER {user_id}"
    confirm = st.text_input(
        f'Tippe `{expected}` um die Löschung freizugeben:',
        placeholder=expected,
        help="Bestätigungsphrase im GitHub-Stil — Groß-/Kleinschreibung wird ignoriert.",
    )

    if st.button(
        "🗑 Endgültig DSGVO-löschen",
        type="primary",
        disabled=confirm.strip().upper() != expected,
    ):
        try:
            report = client.dsgvo_full_delete(int(user_id))
            st.success(
                f"✓ User {user_id} gelöscht.\n\n"
                f"- Pseudonym: `{report['user_email_pseudonym']}`\n"
                f"- Gelöschte Dokumente: {report['deleted_documents']}\n"
                f"- Gelöschte Businesspläne: {report['deleted_business_plans']}\n"
                f"- Pseudonymisierte Token-Logs: {report['pseudonymized_token_logs']}\n"
                f"- Pseudonymisierte Audit-Einträge: {report['pseudonymized_audit_entries']}"
            )
        except APIError as exc:
            st.error(f"Löschung fehlgeschlagen: {exc.detail}")


# ----------------------------------------------------------------------- #
# DSGVO Art. 15 — Datenexport
# ----------------------------------------------------------------------- #

def _render_dsgvo_export(client: APIClient) -> None:
    st.subheader("📥 DSGVO Art. 15 — Auskunftsrecht")

    st.info(
        "Exportiert alle Daten, die wir über einen User gespeichert haben. "
        "Das Ergebnis kann dem Betroffenen als JSON ausgehändigt werden.",
        icon="ℹ️",
    )

    user_id = st.number_input(
        "User-ID für Export",
        min_value=1, step=1,
        key="dsgvo_export_user_id",
    )

    if st.button("📥 Daten exportieren"):
        try:
            data = client.dsgvo_export(int(user_id))
            st.json(data)

            # Auch als Download
            st.download_button(
                "⬇️ Als JSON herunterladen",
                data=json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"),
                file_name=f"dsgvo_export_user_{user_id}.json",
                mime="application/json",
            )
        except APIError as exc:
            st.error(f"Export fehlgeschlagen: {exc.detail}")
