"""
Compliance-Freigaben: Vier-Augen-Antraege einsehen und entscheiden.

Die Seite spricht ausschliesslich mit der API (/approvals). Ob jemand
entscheiden darf, sagt das Backend (can_decide); ueber den eigenen Antrag
entscheidet nie, wer ihn gestellt hat. Nach einer Freigabe fuehrt der Server
das Werkzeug sofort aus, mit den Rechten des Antragstellers.

Analogie: das Schwarze Brett mit dem Posteingang. Jeder sieht, dass Post da
ist; stempeln darf nur, wer zustaendig ist, und nie den eigenen Brief.
"""

import json
from datetime import datetime, timezone

import streamlit as st

from streamlit_app.api_client import APIClient, APIError

WERKZEUGE = {
    "regulation_import": "Regulierungs-Import",
    "search_documents": "Dokumentensuche",
}

ERGEBNIS = {
    "succeeded": ("success", "Freigegeben und ausgeführt."),
    "failed": ("error", "Freigegeben, aber die Ausführung ist fehlgeschlagen."),
    "skipped": ("warning", "Freigegeben, aber nicht ausgeführt."),
}


def _relativ(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    sek = int((datetime.now(timezone.utc) - dt).total_seconds())
    if sek < 60:
        return "vor wenigen Sekunden"
    if sek < 3600:
        return f"vor {sek // 60} Min."
    if sek < 86400:
        return f"vor {sek // 3600} Std."
    return f"vor {sek // 86400} Tagen"


def _fehler(exc: Exception) -> str:
    return getattr(exc, "detail", None) or str(exc)


def _zeige_ergebnis(res: dict) -> None:
    art, text = ERGEBNIS.get(res.get("execution_status") or "", ("info", "Entschieden."))
    getattr(st, art)(f"Antrag #{res.get('id')}: {text}")
    roh = res.get("execution_result")
    if roh:
        try:
            daten = json.loads(roh)
        except ValueError:
            daten = roh
        if isinstance(daten, dict) and daten.get("error"):
            st.caption(f"Grund: {daten['error']}")
        with st.expander("Ergebnis im Detail"):
            st.json(daten) if isinstance(daten, (dict, list)) else st.code(str(daten))


def render() -> None:
    st.header("🛡️ Compliance-Freigaben")

    client = APIClient(token=st.session_state.get("token"))
    ich = (st.session_state.get("user") or {}).get("email", "").lower()

    # Ergebnis der letzten Entscheidung (ueberlebt das Neuladen)
    if "_approval_result" in st.session_state:
        res = st.session_state.pop("_approval_result")
        if res.get("status") == "rejected":
            st.info(f"Antrag #{res.get('id')} wurde abgelehnt.")
        else:
            _zeige_ergebnis(res)

    try:
        daten = client.list_approvals()
    except APIError as exc:
        st.error(f"Anträge konnten nicht geladen werden: {_fehler(exc)}")
        return

    darf = bool(daten.get("can_decide"))
    antraege = daten.get("items") or []

    if darf:
        st.caption(
            "Sie dürfen über Anträge entscheiden. Über eigene Anträge entscheidet "
            "eine andere berechtigte Person (Vier-Augen-Prinzip). Mit der Freigabe "
            "wird der Vorgang sofort ausgeführt."
        )
    else:
        st.info(
            "Sie sehen alle offenen Freigabe-Anträge zur Nachvollziehbarkeit. "
            "Entscheiden können fachliche Freigeber, Compliance-Officer und Administratoren."
        )

    if not antraege:
        st.success("Keine offenen Freigabe-Anträge.")
        return

    n = len(antraege)
    st.write(f"**{n} offener Antrag**" if n == 1 else f"**{n} offene Anträge**")

    for a in antraege:
        with st.container(border=True):
            kopf, status = st.columns([4, 1])
            name = WERKZEUGE.get(a["tool_name"], a["tool_name"])
            kopf.markdown(f"**Antrag #{a['id']}: {name}**")
            kopf.caption(f"von {a['requester_email']} ({a['requester_role']}), {_relativ(a.get('created_at'))}")
            status.markdown(":orange[⏳ offen]")

            if a.get("reason"):
                st.markdown(f"**Begründung:** {a['reason']}")

            if a.get("params") is not None:
                with st.expander("Parameter anzeigen"):
                    st.json(a["params"])
            else:
                st.caption("Die Parameter sehen nur Entscheidungsberechtigte und der Antragsteller.")

            if not darf:
                continue
            if a["requester_email"].lower() == ich:
                st.caption("Ihr eigener Antrag: Die Entscheidung trifft eine andere berechtigte Person.")
                continue

            # Formular: Notiz und Klick werden zusammen uebertragen. Ohne Formular
            # schluckt das Uebernehmen des Notizfelds den ersten Klick.
            with st.form(key=f"form_{a['id']}", border=False):
                notiz = st.text_area("Notiz zur Entscheidung (Pflicht bei Ablehnung)",
                                     key=f"notes_{a['id']}", height=68)
                ok, nein = st.columns(2)
                freigeben = ok.form_submit_button("✅ Freigeben und ausführen", type="primary",
                                                  use_container_width=True)
                ablehnen = nein.form_submit_button("❌ Ablehnen", use_container_width=True)

            if freigeben:
                with st.spinner("Wird freigegeben und ausgeführt ..."):
                    try:
                        st.session_state["_approval_result"] = client.approve_request(a["id"], notiz or None)
                        st.rerun()
                    except APIError as exc:
                        st.error(f"Freigabe fehlgeschlagen: {_fehler(exc)}")
            if ablehnen:
                if not notiz or not notiz.strip():
                    st.error("Für eine Ablehnung ist eine Begründung Pflicht.")
                else:
                    try:
                        st.session_state["_approval_result"] = client.reject_request(a["id"], notiz)
                        st.rerun()
                    except APIError as exc:
                        st.error(f"Ablehnung fehlgeschlagen: {_fehler(exc)}")
