"""
Web-Abruf fuer die Regulierungs-Automation.

Souveraen: NUR oeffentlich zugaengliche Seiten per GET. Keine Credentials,
kein Login, kein Umgehen von Zugangsschranken. Wenn eine Quelle Login
verlangt (401/403 oder erkennbare Login-Seite), scheitert der Abruf
EHRLICH mit einer klaren Meldung -- der Nutzer laedt dann manuell hoch.

Der Inhalt geht danach lokal in die Wissensdatenbank; nach aussen geht nur
die URL. Das verletzt die Datenresidenz-Policy nicht.
"""

from __future__ import annotations

import httpx
from lxml import html as lxml_html


class WebFetchError(Exception):
    """Abruf fehlgeschlagen -- mit menschenlesbarer Begruendung."""


class LoginRequiredError(WebFetchError):
    """Die Quelle ist nicht frei zugaenglich (Login/Paywall)."""


# Grobe Indizien fuer eine Login-/Paywall-Seite im HTML.
_LOGIN_HINTS = (
    "login", "anmelden", "sign in", "passwort", "password",
    "paywall", "subscribe", "abonnieren", "zugang erforderlich",
)

_MAX_BYTES = 5_000_000  # 5 MB Deckel -- Regulierungsseiten sind kleiner
_TIMEOUT = 20


def fetch_clean_text(url: str) -> dict:
    """
    Holt eine oeffentliche Seite und gibt sauberen Text zurueck.

    Returns:
        {"url": str, "title": str, "text": str, "length": int}

    Raises:
        LoginRequiredError: Quelle verlangt Login / ist nicht frei.
        WebFetchError: sonstiger Abruf-/Extraktionsfehler.
    """
    if not url.startswith(("http://", "https://")):
        raise WebFetchError("Nur http(s)-URLs werden unterstuetzt.")

    try:
        with httpx.Client(follow_redirects=True, timeout=_TIMEOUT) as client:
            resp = client.get(url, headers={"User-Agent": "Verinaris/1.0 (Regulierungs-Import)"})
    except httpx.RequestError as exc:
        raise WebFetchError(f"Seite nicht erreichbar: {exc}") from exc

    if resp.status_code in (401, 403):
        raise LoginRequiredError(
            "Diese Quelle ist nicht frei zugaenglich (Login erforderlich). "
            "Bitte das Dokument manuell herunterladen und hochladen."
        )
    if resp.status_code >= 400:
        raise WebFetchError(f"Abruf fehlgeschlagen (HTTP {resp.status_code}).")

    ctype = resp.headers.get("content-type", "")
    if "html" not in ctype and "text" not in ctype:
        raise WebFetchError(
            f"Inhalt ist kein HTML/Text ({ctype or 'unbekannt'}). "
            "Fuer PDFs bitte den Datei-Upload nutzen."
        )

    raw = resp.content[:_MAX_BYTES]
    try:
        doc = lxml_html.fromstring(raw)
    except Exception as exc:
        raise WebFetchError(f"HTML konnte nicht gelesen werden: {exc}") from exc

    # Titel
    title_el = doc.find(".//title")
    title = (title_el.text if title_el is not None and title_el.text else url).strip()

    # Skripte/Styles/Navigation raus, dann Text sammeln
    for bad in doc.xpath("//script | //style | //nav | //footer | //header"):
        bad.getparent().remove(bad)
    text = " ".join(t.strip() for t in doc.xpath("//body//text()") if t.strip())

    # Login-Seite erkennen: sehr wenig Text + Login-Indizien
    low = text.lower()
    if len(text) < 400 and any(h in low for h in _LOGIN_HINTS):
        raise LoginRequiredError(
            "Diese Quelle scheint einen Login zu verlangen (kaum frei "
            "lesbarer Inhalt). Bitte das Dokument manuell hochladen."
        )

    if len(text) < 100:
        raise WebFetchError(
            "Kaum lesbarer Text gefunden. Moeglicherweise laedt die Seite "
            "Inhalte per JavaScript nach -- bitte manuell hochladen."
        )

    return {"url": url, "title": title, "text": text, "length": len(text)}
