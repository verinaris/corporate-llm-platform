"""
Gemeinsamer Passwort-Generator fuer Frontend-Stellen (User-Anlage,
Passwort-Aendern). Eine Wahrheit statt zwei Kopien.
"""

import secrets
import string

PASSWORT_LAENGE = 16


def neues_passwort(laenge: int = PASSWORT_LAENGE) -> str:
    """
    Zufallspasswort aus Buchstaben und Ziffern.

    secrets statt random: random ist bei bekanntem Startwert vorhersagbar,
    secrets nicht. Sonderzeichen bewusst weggelassen -- das Passwort wird
    vorgelesen oder per Mail verschickt, da ist Verwechslungsfreiheit mehr
    wert als zwei Bit Entropie.
    """
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(laenge))
