"""Tests fuer die Lizenz pro User (LICENSED-Zweig in get_user_status)."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.services.trial import TrialStatus, get_user_status


def _user(trial_started_at=None, license_valid_until=None):
    """Minimaler User-Stub — get_user_status liest nur Attribute."""
    return SimpleNamespace(
        trial_started_at=trial_started_at,
        license_valid_until=license_valid_until,
    )


def test_lizenz_gilt_auch_ohne_ersten_login():
    """Der wichtigste Fall: Lizenz schlaegt die None-Pruefung der Testphase."""
    ergebnis = get_user_status(
        _user(license_valid_until=datetime.now(timezone.utc) + timedelta(days=365))
    )
    assert ergebnis["status"] == TrialStatus.LICENSED


def test_lizenz_schlaegt_abgelaufene_testphase():
    ergebnis = get_user_status(
        _user(
            trial_started_at=datetime.now(timezone.utc) - timedelta(days=99),
            license_valid_until=datetime.now(timezone.utc) + timedelta(days=30),
        )
    )
    assert ergebnis["status"] == TrialStatus.LICENSED
    assert ergebnis["days_remaining"] == 29


def test_abgelaufene_lizenz_faellt_auf_testphase_zurueck():
    """Keine Sperre — abgelaufene Lizenz verhaelt sich wie gar keine."""
    ergebnis = get_user_status(
        _user(
            trial_started_at=datetime.now(timezone.utc) - timedelta(days=99),
            license_valid_until=datetime.now(timezone.utc) - timedelta(days=1),
        )
    )
    assert ergebnis["status"] == TrialStatus.EXPIRED


def test_ohne_lizenz_unveraendert():
    """Regressionsschutz: Bestandsuser verhalten sich exakt wie vorher."""
    ergebnis = get_user_status(
        _user(trial_started_at=datetime.now(timezone.utc) - timedelta(days=1))
    )
    assert ergebnis["status"] == TrialStatus.ACTIVE


def test_naives_datum_bricht_nicht():
    """SQLite liefert datetimes naiv zurueck — _ensure_utc muss greifen."""
    naiv = (datetime.now(timezone.utc) + timedelta(days=10)).replace(tzinfo=None)
    ergebnis = get_user_status(_user(license_valid_until=naiv))
    assert ergebnis["status"] == TrialStatus.LICENSED
