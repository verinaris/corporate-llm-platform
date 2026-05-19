"""
Datenbank-Setup (SQLite via SQLModel).

Erzeugt die Tabellen beim Start, falls sie noch nicht existieren.
Liefert eine Session, mit der die App auf die DB zugreift.

Analogie: `engine` ist die Türklinke zur DB, `session` ist ein
einzelner Besuch im Archivraum.
"""

import os
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings

settings = get_settings()

# Sicherstellen, dass der data/-Ordner existiert (bei SQLite-File-DB)
if settings.database_url.startswith("sqlite:///"):
    db_path = settings.database_url.replace("sqlite:///", "")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

# Engine = DB-Verbindungspool
engine = create_engine(
    settings.database_url,
    echo=False,  # auf True setzen, um SQL-Queries zu loggen (Debug)
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)


def init_db() -> None:
    """Erzeugt alle Tabellen, die als SQLModel definiert sind."""
    # Wichtig: Modelle importieren, damit SQLModel sie kennt
    from app import models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI-Dependency für DB-Session."""
    with Session(engine) as session:
        yield session
