"""
AutomationTool — Basistyp fuer generierende Automationen mit Human-in-the-Loop.

Unterschied zu einem gewoehnlichen BaseTool: Eine Automation erzeugt einen
ENTWURF (LinkedIn-Post, Regulierungs-Zusammenfassung, SOP), den ein
qualifizierter Mensch pruefen muss, BEVOR er wirkt. Man kann einen Text nicht
freigeben, bevor er existiert -- deshalb zwei Stufen:

    generate()  -> erzeugt den Entwurf. Laeuft SOFORT, hat keinen
                   Aussen-Nebeneffekt (nichts wird gepostet/veroeffentlicht).
    execute()   -> finalisiert/veroeffentlicht den FREIGEGEBENEN Entwurf.
                   Freigabepflichtig ueber den bestehenden Approval-Flow.

Der Freigeber sieht zwischen den Stufen den fertigen Entwurf und entscheidet.

Analogie: generate() schreibt den Brief, execute() wirft ihn in den Kasten.
Unterschrieben wird dazwischen -- und zwar der fertige Brief, nicht die Absicht.

WICHTIG -- die Freigabepflicht ist NICHT abschaltbar:
requires_human_oversight ist hier eine property ohne Setter und immer True.
Eine konkrete Automation kann sie nicht ueberschreiben. Das ist der Kern des
Versprechens: eine generierende Automation OHNE Freigabe soll gar nicht
baubar sein.
"""

from abc import abstractmethod
from typing import Any

from app.tools.base import BaseTool


class AutomationTool(BaseTool):
    """
    Basistyp fuer freigabepflichtige, generierende Automationen.

    Unterklassen implementieren generate() und execute(). allowed_roles,
    name, description und parameters_schema werden wie bei jedem Tool gesetzt.
    """

    @property
    def requires_human_oversight(self) -> bool:
        """
        Immer True und nicht ueberschreibbar. Eine generierende Automation
        ohne menschliche Freigabe soll nicht existieren koennen.
        """
        return True

    @abstractmethod
    def generate(self, params: dict, user_id: int | None = None) -> dict[str, Any]:
        """
        Erzeugt den Entwurf, den ein Mensch anschliessend prueft.

        Muss NEBENWIRKUNGSFREI nach aussen sein: hier wird nichts gepostet,
        versendet oder veroeffentlicht. Nur der Entwurf entsteht.

        Returns:
            dict mit mindestens einem 'draft'-Feld (der pruefbare Entwurf)
            und optional 'meta' (Quellen, Modell, Warnungen fuer den Freigeber).
        """
        raise NotImplementedError

    @abstractmethod
    def execute(self, params: dict, user_id: int | None = None) -> dict[str, Any]:
        """
        Finalisiert/veroeffentlicht den FREIGEGEBENEN Entwurf.

        Wird erst nach erteilter Freigabe ueber den Approval-Flow aufgerufen.
        params enthaelt den freigegebenen Entwurf (bzw. dessen Referenz).
        """
        raise NotImplementedError
