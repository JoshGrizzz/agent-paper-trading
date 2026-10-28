"""Private runner profile for rollout-specific account and isolation settings."""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


class ProfileError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class RolloutProfile:
    initial_cash: Decimal = Decimal("100000.00")
    workspace_name: str | None = None
    allow_isolated_python: bool = False
    cohort: str | None = None
    predecessor: str | None = None
    overnight_smoke_until_next_noon: bool = False

    @property
    def is_v2(self) -> bool:
        return self.workspace_name is not None

    def workspace(self, rollout_directory: Path) -> Path:
        if self.workspace_name is None:
            return rollout_directory
        return rollout_directory / self.workspace_name


def profile_path(rollout_directory: Path) -> Path:
    return rollout_directory / ".runner" / "profile.json"


def load_profile(rollout_directory: Path) -> RolloutProfile:
    path = profile_path(rollout_directory)
    if not path.exists():
        return RolloutProfile()
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ProfileError(f"invalid rollout profile: {path}") from error
    if not isinstance(document, dict) or document.get("schema_version") != 1:
        raise ProfileError(f"invalid rollout profile schema: {path}")
    try:
        initial_cash = Decimal(document["initial_cash"])
    except (KeyError, TypeError, InvalidOperation) as error:
        raise ProfileError("rollout profile initial_cash is invalid") from error
    if not initial_cash.is_finite() or initial_cash <= 0:
        raise ProfileError("rollout profile initial_cash must be positive and finite")
    workspace_name = document.get("workspace")
    if workspace_name is not None and workspace_name != "workspace":
        raise ProfileError("rollout profile workspace must be 'workspace'")
    allow_python = document.get("allow_isolated_python", False)
    if not isinstance(allow_python, bool):
        raise ProfileError("allow_isolated_python must be boolean")
    if allow_python and workspace_name != "workspace":
        raise ProfileError("isolated Python requires an isolated workspace")
    overnight_smoke = document.get(
        "overnight_smoke_until_next_noon", False
    )
    if not isinstance(overnight_smoke, bool):
        raise ProfileError(
            "overnight_smoke_until_next_noon must be boolean"
        )
    cohort = document.get("cohort")
    predecessor = document.get("predecessor")
    if cohort is not None and not isinstance(cohort, str):
        raise ProfileError("profile cohort must be a string")
    if predecessor is not None and not isinstance(predecessor, str):
        raise ProfileError("profile predecessor must be a string")
    return RolloutProfile(
        initial_cash=initial_cash,
        workspace_name=workspace_name,
        allow_isolated_python=allow_python,
        cohort=cohort,
        predecessor=predecessor,
        overnight_smoke_until_next_noon=overnight_smoke,
    )


def profile_document(
    *, initial_cash: Decimal, cohort: str, predecessor: str,
    overnight_smoke_until_next_noon: bool = False,
) -> dict[str, Any]:
    if not initial_cash.is_finite() or initial_cash <= 0:
        raise ValueError("initial_cash must be positive and finite")
    document = {
        "schema_version": 1,
        "initial_cash": str(initial_cash),
        "workspace": "workspace",
        "allow_isolated_python": True,
        "cohort": cohort,
        "predecessor": predecessor,
    }
    if overnight_smoke_until_next_noon:
        document["overnight_smoke_until_next_noon"] = True
    return document
