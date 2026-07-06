"""
Compliance-Dashboard — Vier-Augen-Freigaben.

Alle User koennen offene Antraege einsehen (Transparenz).
Nur Rolle 'compliance-officer' und 'admin' koennen entscheiden.
"""

from datetime import datetime, timezone
import json

import streamlit as st

from app.services.approval_request import (
    approve_request,
    list_pending,
    reject_request,
    get_request,
)
from app.models import ApprovalStatus


def _format_relative(dt: datetime) -> str:
    """Zeigt 'vor X Minuten/Stunden' fuer Benutzerfreundlichkeit."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = datetime.now(timezone.utc) - dt
    seconds = int(diff.total_seconds())
    if seconds < 60:
        return f"vor {seconds}s"
    if seconds < 3600:
        return f"vor {seconds // 60} Min"
    if seconds < 86400:
        return f"vor {seconds // 3600} Std"
    return f"vor {seconds // 86400} Tagen"


def _may_decide(user) -> bool:
    """Prueft, ob der User entscheiden darf."""
    if not user:
        return False
    role = getattr(user, "role", None)
    if role is None:
        return False
    role_value = role.value if hasattr(role, "value") else str(role)
    return role_value in ("admin", "compliance-officer")


def render():
    """Haupt-Render-Funktion fuer das Compliance-Dashboard."""
    st.header("🛡️ Compliance-Freigaben")

    user = st.session_state.get("current_user")
    can_decide = _may_decide(user)

    if not can_decide:
        st.info(
            "Sie sehen alle offenen Freigabe-Antraege zur Nachvollziehbarkeit. "
            "Entscheidungen koennen nur Compliance-Officer treffen."
        )

    # Offene Antraege laden
    try:
        pending = list_pending()
    except Exception as exc:
        st.error(f"Antraege konnten nicht geladen werden: {exc}")
        return

    if not pending:
        st.success("Keine offenen Freigabe-Antraege.")
        return

    st.write(f"**{len(pending)} offene Antraege**")
    st.divider()

    for req in pending:
        with st.container(border=True):
            # Kopfzeile
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**Antrag #{req.id} — {req.tool_name}**")
                st.caption(
                    f"von {req.requester_email} ({req.requester_role}) "
                    f"— {_format_relative(req.created_at)}"
                )
            with col2:
                st.markdown(f":orange[⏳ {req.status.value}]")

            # Grund (falls angegeben)
            if req.reason:
                st.markdown(f"**Begruendung:** {req.reason}")

            # Params (aufklappbar)
            with st.expander("Tool-Parameter anzeigen"):
                try:
                    params = json.loads(req.params_json)
                    st.json(params)
                except Exception:
                    st.code(req.params_json)

            # Entscheidungs-Buttons (nur wenn erlaubt)
            if can_decide:
                st.divider()
                notes_key = f"notes_{req.id}"
                notes = st.text_area(
                    "Entscheidungs-Notiz (Pflicht bei Ablehnung)",
                    key=notes_key,
                    height=68,
                )

                col_ok, col_no = st.columns(2)
                with col_ok:
                    if st.button(
                        "✅ Freigeben",
                        key=f"approve_{req.id}",
                        type="primary",
                        use_container_width=True,
                    ):
                        try:
                            _, token_str = approve_request(
                                request_id=req.id,
                                approver_email=user.email,
                                approver_role=user.role.value,
                                decision_notes=notes or None,
                            )
                            st.success(
                                f"Freigegeben. Token: {token_str[:16]}..."
                            )
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Fehler: {exc}")

                with col_no:
                    if st.button(
                        "❌ Ablehnen",
                        key=f"reject_{req.id}",
                        use_container_width=True,
                    ):
                        if not notes or not notes.strip():
                            st.error("Ablehnungs-Grund ist Pflicht.")
                        else:
                            try:
                                reject_request(
                                    request_id=req.id,
                                    approver_email=user.email,
                                    approver_role=user.role.value,
                                    decision_notes=notes,
                                )
                                st.success("Abgelehnt.")
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Fehler: {exc}")
