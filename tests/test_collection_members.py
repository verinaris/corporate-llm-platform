"""Tests fuer das Datenmodell der Mandantentrennung (E1)."""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, create_engine

from app.models import (
    AuditAction,
    CollectionAccessLevel,
    CollectionMember,
    DocumentCollection,
    User,
)


def _session():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_sammlung_standardmaessig_geschlossen():
    coll = DocumentCollection(name="akte-mueller", created_by="a@kanzlei.de")
    assert coll.open_for_all is False


def test_mitglied_standardstufe_lesen():
    m = CollectionMember(collection="x", user_id=1, granted_by="admin@x.de")
    assert m.level == CollectionAccessLevel.READ


def test_mitglied_pro_sammlung_eindeutig():
    s = _session()
    s.add(User(email="u@x.de", password_hash="h"))  # pragma: allowlist secret
    s.add(DocumentCollection(name="akte", created_by="a@x.de"))
    s.commit()
    s.add(CollectionMember(collection="akte", user_id=1, granted_by="a@x.de"))
    s.commit()
    s.add(CollectionMember(collection="akte", user_id=1, granted_by="a@x.de",
                           level=CollectionAccessLevel.MAINTAIN))
    with pytest.raises(IntegrityError):
        s.commit()


def test_neue_audit_aktionen_vorhanden():
    for name in ("COLLECTION_ACCESS_DENIED", "COLLECTION_ACCESS_GRANTED",
                 "COLLECTION_ACCESS_REVOKED", "COLLECTION_VISIBILITY_CHANGED"):
        assert hasattr(AuditAction, name)
