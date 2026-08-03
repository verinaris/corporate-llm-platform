"""
KI-Transparenzhinweis (EU AI Act, Art. 50).

Weist jeden Nutzer darauf hin, dass er mit einem KI-System interagiert.
Dauerhaft sichtbar (Variante B). Spaeter ggf. abgeloest durch eine
einmalige, dokumentierte Bestaetigung (Variante A).

Wird -- wie der Trial-Banner -- oben auf der Seite gerendert.
"""

import streamlit as st

# Zentral, damit der Text an einer Stelle steht und juristisch leicht
# anpassbar bleibt.
_AI_DISCLOSURE_TEXT = (
    "🤖 **Hinweis:** Sie interagieren mit einem KI-System. Antworten koennen "
    "Fehler enthalten und ersetzen keine fachliche, rechtliche oder "
    "medizinische Beratung. Pruefen Sie Ergebnisse vor einer Verwendung."
)


def render_ai_disclosure_banner() -> None:
    """Zeigt den dauerhaften KI-Transparenzhinweis oben auf der Seite."""
    st.info(_AI_DISCLOSURE_TEXT)
