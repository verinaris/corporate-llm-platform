"""Tests fuer die Hausordnung der Mandantentrennung (E2)."""

from sqlmodel import Session, SQLModel, create_engine

from app.auth.permissions import (
    can_maintain_collection,
    can_manage_collection_access,
    can_read_collection,
    collection_level,
)
from app.models import (
    CollectionAccessLevel,
    CollectionMember,
    DocumentCollection,
    User,
    UserRole,
)
from app.services.collection_access import get_collection_level, readable_collections


# ---------- reine Regel ----------

def test_besitzer_ist_owner_auch_bei_grossschreibung():
    assert collection_level("A@Kanzlei.de", "a@kanzlei.de", None, False) == "owner"


def test_fremder_ohne_eintrag_hat_keinen_zugriff():
    assert collection_level("b@x.de", "a@x.de", None, False) is None


def test_mitglied_stufen():
    assert collection_level("b@x.de", "a@x.de", CollectionAccessLevel.READ, False) == "read"
    assert collection_level("b@x.de", "a@x.de", CollectionAccessLevel.MAINTAIN, False) == "maintain"


def test_fuer_alle_lesbar_gibt_nur_lesen():
    assert collection_level("b@x.de", "a@x.de", None, True) == "read"
    # Pflege-Mitglied verliert durch "fuer alle" nichts
    assert collection_level("b@x.de", "a@x.de", CollectionAccessLevel.MAINTAIN, True) == "maintain"


def test_lesen_und_pflegen():
    assert not can_read_collection(None)
    assert can_read_collection("read") and not can_maintain_collection("read")
    assert can_maintain_collection("maintain") and can_maintain_collection("owner")


def test_nur_admin_vergibt_rechte():
    assert can_manage_collection_access(UserRole.ADMIN)
    for rolle in ("compliance-officer", "qualified-reviewer", "user"):
        assert not can_manage_collection_access(rolle)


# ---------- DB-Nachschlagen ----------

def _setup():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    s = Session(engine)
    admin = User(email="admin@x.de", password_hash="h", role=UserRole.ADMIN)  # pragma: allowlist secret
    anna = User(email="anna@x.de", password_hash="h")  # pragma: allowlist secret
    bert = User(email="bert@x.de", password_hash="h")  # pragma: allowlist secret
    s.add_all([admin, anna, bert])
    s.add_all([
        DocumentCollection(name="akte-anna", created_by="anna@x.de"),
        DocumentCollection(name="ema-leitlinien", created_by="anna@x.de", open_for_all=True),
        DocumentCollection(name="geteilt", created_by="anna@x.de"),
    ])
    s.commit()
    s.add(CollectionMember(collection="geteilt", user_id=bert.id, granted_by="admin@x.de"))
    s.commit()
    return s, admin, anna, bert


def test_admin_liest_keine_fremden_sammlungen():
    s, admin, anna, bert = _setup()
    assert readable_collections(s, admin) == {"ema-leitlinien"}
    assert get_collection_level(s, admin, "akte-anna") is None


def test_besitzer_sieht_alles_eigene():
    s, admin, anna, bert = _setup()
    assert readable_collections(s, anna) == {"akte-anna", "ema-leitlinien", "geteilt"}


def test_mitglied_sieht_geteilte_und_offene():
    s, admin, anna, bert = _setup()
    assert readable_collections(s, bert) == {"ema-leitlinien", "geteilt"}
    assert get_collection_level(s, bert, "geteilt") == "read"


def test_unbekannte_sammlung_ist_geschlossen():
    s, admin, anna, bert = _setup()
    assert get_collection_level(s, anna, "gibt-es-nicht") is None
