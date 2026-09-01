from __future__ import annotations
import sqlite3

import pytest

from app.logic.repositories import ProgramRepository, SettingsRepository, WorkoutRepository
from app.logic.schema import create_schema
from app.logic.services import WorkoutService
from app.logic.session_state import SessionState


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    create_schema(connection)
    yield connection
    connection.close()


@pytest.fixture
def program_repo(conn):
    return ProgramRepository(conn)


@pytest.fixture
def workout_repo(conn):
    return WorkoutRepository(conn)


@pytest.fixture
def settings_repo(conn):
    return SettingsRepository(conn)


@pytest.fixture
def service(program_repo, workout_repo, settings_repo):
    return WorkoutService(program_repo, workout_repo, settings_repo, SessionState())
