"""
Trial-Banner — Zeigt den Trial-Status oben in jeder Seite.

Pulled den Status vom FastAPI-Backend (/api/trial/status, öffentlich)
und rendert je nach Status:
- 🟢 active        → st.info
- 🟡 expiring_soon → st.warning
- 🔴 expired       → st.error
- ✅ licensed      → st.success

Bei Fehler (Backend down, Network) wird der Banner stillschweigend
übersprungen — die App soll auch ohne Trial-Banner funktionieren.
"""

from typing import Optional

import streamlit as st

from streamlit_app.api_client import APIClient


def render_trial_banner() -> None:
    """
    Zeigt den Trial-Banner oben auf der aktuellen Seite an.

    Diese Funktion sollte als ERSTES nach dem st.title()-Aufruf
    in jeder Seite aufgerufen werden.

    Defensiv: Bei Backend-Fehlern wird kein Banner angezeigt,
    aber kein Crash.
    """
    status = _fetch_trial_status()
    if not status:
        return  # Backend down oder Netzwerkfehler — kein Banner

    state = status.get("status", "")
    message = status.get("message", "")

    if not message:
        return

    # Style je nach Status
    if state == "active":
        st.info(f"🟢 {message}")
    elif state == "expiring_soon":
        st.warning(f"🟡 {message}")
    elif state == "expired":
        st.error(f"🔴 {message}")
    elif state == "licensed":
        st.success(f"✅ {message}")


def _fetch_trial_status() -> Optional[dict]:
    """
    Holt den Trial-Status vom Backend.

    Returns:
        Status-Dict oder None bei Fehler.
    """
    try:
        client = APIClient()  # Public Endpoint — kein Token nötig
        return client.get_trial_status()
    except Exception:
        # Bewusst alle Exceptions schlucken — Banner ist Add-on
        return None
