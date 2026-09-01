from __future__ import annotations
import sqlite3
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class NextTarget:
    weight: Optional[float]
    sets: int
    reps: int
    text: str


@dataclass
class Exercise:
    id: int
    program_id: int
    name: str
    next_target: Optional[NextTarget] = None


@dataclass
class Program:
    id: int
    name: str
    progression_type: str
    exercises: List[Exercise] = field(default_factory=list)


@dataclass
class SetEntry:
    id: int
    type: str
    weight: str
    reps: str


@dataclass
class SessionExercise:
    exercise_id: int
    exercise_name: str
    sets: List[SetEntry] = field(default_factory=list)


@dataclass
class WorkoutSession:
    id: int
    program_id: Optional[int]
    program_name: Optional[str]
    date: str
    exercises: List[SessionExercise] = field(default_factory=list)


def row_to_next_target(row: sqlite3.Row) -> Optional[NextTarget]:
    if row["next_target_text"] is None:
        return None
    return NextTarget(
        weight=row["next_target_weight"],
        sets=row["next_target_sets"],
        reps=row["next_target_reps"],
        text=row["next_target_text"],
    )


def row_to_exercise(row: sqlite3.Row) -> Exercise:
    return Exercise(
        id=row["id"],
        program_id=row["program_id"],
        name=row["name"],
        next_target=row_to_next_target(row),
    )


def row_to_program(row: sqlite3.Row, exercises: List[Exercise]) -> Program:
    return Program(
        id=row["id"],
        name=row["name"],
        progression_type=row["progression_type"],
        exercises=exercises,
    )


def row_to_set_entry(row: sqlite3.Row) -> SetEntry:
    return SetEntry(id=row["set_id"], type=row["type"], weight=row["weight"], reps=row["reps"])
