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
    "🤖 **Hinweis:** Sie interagieren mit einem KI-System. Antworten können "
    "Fehler enthalten und ersetzen keine fachliche, rechtliche oder "
    "medizinische Beratung. Prüfen Sie Ergebnisse vor einer Verwendung."
)


def render_ai_disclosure_banner(already_acknowledged: bool = False) -> None:
    """
    Zeigt den dauerhaften KI-Transparenzhinweis oben auf der Seite.

    Variante A loest Variante B ab: wer den Hinweis dokumentiert bestaetigt
    hat (already_acknowledged=True), braucht den Dauerbanner nicht mehr.
    Am Login-Fenster (kein User) bleibt der Banner sichtbar.
    """
    if already_acknowledged:
        return
    st.info(_AI_DISCLOSURE_TEXT)
