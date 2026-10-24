"""
🗄️ Aufbewahrung: Fristen, Löschsperre, endgültiges Löschen, Löschnachweise.

Nur Compliance-Officer und Admin. Die Seite zeigt ausschließlich Metadaten
(Namen, Fristen, Anzahl), nie Inhalte.

Analogie: der Aufkleber auf dem Archivkarton und das Vernichtungsprotokoll.
"""

from datetime import date

import streamlit as st

from streamlit_app.api_client import APIClient, APIError

STATUS_ICON = {
    "gesperrt": "🔒", "frist_unbekannt": "❔", "frist_laeuft": "⏳",
    "nicht_archiviert": "📂", "loeschbar": "🗑",
}


def _datum(iso) -> str:
    if not iso:
        return ""
    try:
        return date.fromisoformat(str(iso)[:10]).strftime("%d.%m.%Y")
    except ValueError:
        return str(iso)


def _do(action, erfolg) -> None:
    try:
        result = action()
    except APIError as e:
        st.error(f"Fehlgeschlagen: {e.detail}")
        return
    st.session_state["retention_msg"] = erfolg(result) if callable(erfolg) else erfolg
    st.rerun()


def render() -> None:
    st.title("🗄️ Aufbewahrung")
    st.caption(
        "Aufbewahrungsfristen, Löschsperren und endgültiges Löschen. Sie sehen hier nur "
        "Namen, Fristen und Anzahlen, keine Inhalte. Jede Änderung steht mit Begründung "
        "im Audit-Log."
    )
    me = st.session_state.get("user", {})
    if me.get("role") not in ("admin", "compliance-officer"):
        st.error("Kein Zugriff. Diese Seite ist nur für Compliance-Officer und Admins.")
        return
    if "retention_msg" in st.session_state:
        st.success(st.session_state.pop("retention_msg"))

    client = APIClient(token=st.session_state.get("token"))
    try:
        rows = client.list_retention()
        records = client.list_deletion_records()
    except APIError as e:
        st.error(f"Daten konnten nicht geladen werden: {e.detail}")
        return
    if not rows:
        st.info("Noch keine Sammlungen vorhanden.")
    else:
        _render_overview(client, rows)
    st.markdown("---")
    _render_records(records)


def _render_overview(client: APIClient, rows: list[dict]) -> None:
    loeschbar = [r["name"] for r in rows if r["status"] == "loeschbar"]
    if loeschbar:
        st.info(f"{len(loeschbar)} Sammlung(en) können endgültig gelöscht werden: " + ", ".join(loeschbar))

    st.dataframe(
        [{
            "Sammlung": r["name"],
            "Besitzer": r["created_by"],
            "Archiviert": "ja" if r["archived_at"] else "nein",
            "Aufbewahren bis": _datum(r["retain_until"]) or "unbekannt",
            "Löschsperre": "🔒 ja" if r["legal_hold"] else "nein",
            "Dokumente": r["document_count"],
            "Status": f"{STATUS_ICON.get(r['status'], '')} {r['status_label']}",
        } for r in rows],
        use_container_width=True, hide_index=True,
    )

    st.markdown("---")
    wahl = st.selectbox("Sammlung bearbeiten", [r["name"] for r in rows])
    c = next(r for r in rows if r["name"] == wahl)
    st.markdown(f"**Status:** {STATUS_ICON.get(c['status'], '')} {c['status_label']}")

    st.markdown("**Aufbewahrungsfrist**")
    aktuell = date.fromisoformat(c["retain_until"]) if c["retain_until"] else None
    # Auswahl AUSSERHALB des Formulars: das Datumsfeld erscheint nur, wenn es auch zaehlt.
    # (Vorher: vorbelegtes Haekchen "unbekannt" hat ein gewaehltes Datum still ignoriert.)
    art = st.radio(
        "Frist", ["Datum festlegen", "Unbekannt (kein endgültiges Löschen möglich)"],
        index=0 if aktuell else 1, horizontal=True, key=f"frist-art-{wahl}",
    )
    with st.form(f"frist-{wahl}"):
        if art == "Datum festlegen":
            datum = st.date_input("Aufbewahren bis (einschließlich)", value=aktuell or date.today(),
                                  min_value=date(1990, 1, 1), max_value=date(2100, 12, 31),
                                  format="DD.MM.YYYY")
        else:
            datum = None
            st.caption("Die Frist wird auf „unbekannt“ gesetzt.")
        grund = st.text_input("Begründung (Pflicht, z. B. Rechtsgrundlage)", key=f"frist-grund-{wahl}")
        if st.form_submit_button("Frist übernehmen"):
            neu = datum.isoformat() if datum else None
            _do(lambda: client.set_retention(wahl, neu, grund),
                f"Frist für '{wahl}': " + (_datum(neu) if neu else "unbekannt") + ".")

    with st.form(f"hold-{wahl}"):
        st.markdown("**Löschsperre (Legal Hold)**")
        if c["legal_hold"] and c.get("legal_hold_reason"):
            st.caption(f"Aktueller Grund: {c['legal_hold_reason']}")
        sperre = st.checkbox("Löschsperre aktiv (blockiert endgültiges Löschen, unabhängig von der Frist)",
                             value=c["legal_hold"])
        grund = st.text_input("Begründung (Pflicht)", key=f"hold-grund-{wahl}")
        if st.form_submit_button("Löschsperre übernehmen") and sperre != c["legal_hold"]:
            _do(lambda: client.set_legal_hold(wahl, sperre, grund),
                f"Löschsperre für '{wahl}' " + ("gesetzt." if sperre else "aufgehoben."))

    st.markdown("**Endgültig löschen**")
    if c["status"] != "loeschbar":
        st.caption(
            f"Nicht möglich, Status: {c['status_label']}. Voraussetzungen: Sammlung archiviert, "
            "Frist abgelaufen, keine Löschsperre."
        )
        return
    with st.form(f"purge-{wahl}", clear_on_submit=True):
        st.warning(
            f"Löscht '{wahl}' mit {c['document_count']} Dokument(en) **unwiderruflich**: "
            "Suchindex, Originaldateien, Einträge und Rechte. Zurück bleibt nur der Löschnachweis "
            "(ohne Inhalt). Eine **andere Person** muss den Antrag im Reiter Freigaben freigeben."
        )
        grund = st.text_input("Begründung (Pflicht)", key=f"purge-grund-{wahl}")
        ok = st.checkbox(f"Ich beantrage die endgültige Löschung von '{wahl}'", key=f"purge-ok-{wahl}")
        if st.form_submit_button("Löschantrag stellen", type="primary"):
            if not ok:
                st.error("Bitte zuerst bestätigen.")
            else:
                _do(lambda: client.request_purge(wahl, grund),
                    lambda r: f"Löschantrag #{r.get('approval_id')} für '{wahl}' gestellt. "
                              "Er wartet jetzt im Reiter Freigaben auf eine zweite Person.")


def _render_records(records: list[dict]) -> None:
    st.subheader("Löschnachweise")
    st.caption("Belegt, was wann auf wessen Antrag und mit wessen Freigabe gelöscht wurde. Ohne Inhalt.")
    if not records:
        st.caption("Bisher wurde nichts endgültig gelöscht.")
        return
    st.dataframe(
        [{
            "Sammlung": r["collection"],
            "Gelöscht am": _datum(r["deleted_at"]),
            "Dokumente": r["document_count"],
            "Größe (MB)": round((r["size_bytes"] or 0) / (1024 * 1024), 2),
            "Frist war": _datum(r["retain_until"]),
            "Beantragt von": r["requested_by"],
            "Freigegeben von": r["approved_by"] or "",
            "Antrag #": r["approval_id"],
            "Begründung": r["reason"] or "",
            "Prüfsummen": len(r["content_hashes"]),
        } for r in records],
        use_container_width=True, hide_index=True,
    )
