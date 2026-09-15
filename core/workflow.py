from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class Stage(str, Enum):
    DISCOVER = "discover"
    NORMALIZE = "normalize"
    SCORE = "score"
    SIMULATE = "simulate"
    SELECT = "select"
    CREATE = "create"
    EXPERIMENT = "experiment"
    PUBLISH = "publish"
    MEASURE = "measure"
    LEARN = "learn"
    OPTIMIZE = "optimize"
    COMPLETE = "complete"
    BLOCKED = "blocked"


ORDER = tuple(Stage)


@dataclass
class WorkflowState:
    run_id: str
    stage: Stage = Stage.DISCOVER
    attempts: int = 0
    last_error: str | None = None
    completed: list[Stage] | None = None

    def __post_init__(self) -> None:
        if self.completed is None:
            self.completed = []

    def advance(self, next_stage: Stage) -> None:
        if self.stage in {Stage.COMPLETE, Stage.BLOCKED}:
            raise ValueError("workflow is terminal")
        self.attempts = 0
        self.last_error = None
        self.completed.append(self.stage)
        self.stage = next_stage

    def fail(self, error: str, *, terminal: bool = False) -> None:
        self.attempts += 1
        self.last_error = error[:1000]
        if terminal:
            self.stage = Stage.BLOCKED

    def retryable(self, max_attempts: int = 3) -> bool:
        return self.attempts < max(1, max_attempts) and self.stage not in {Stage.COMPLETE, Stage.BLOCKED}

    def snapshot(self) -> dict:
        return {"run_id": self.run_id, "stage": self.stage.value, "attempts": self.attempts,
                "last_error": self.last_error, "completed": [s.value for s in self.completed or []]}


def validate_path(stages: Iterable[Stage]) -> bool:
    """Validate that a proposed execution path never moves backwards or repeats stages."""
    values = list(stages)
    positions = {stage: i for i, stage in enumerate(ORDER)}
    indexes = [positions[s] for s in values]
    return len(indexes) == len(set(indexes)) and indexes == sorted(indexes)
