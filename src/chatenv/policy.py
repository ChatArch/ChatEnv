"""Runtime policy for ChatEnv's missing-input prompts.

This module intentionally reads only the active ChatArch profile.  It does not
load profile values into ``os.environ`` or into ``EnvField.value`` state.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from .configs import ChatArchConfig
from .paths import get_paths
from .store import EnvStore


AUTO_PROMPT_ENV_VAR = "CHATARCH_AUTO_PROMPT"
AUTO_PROMPT_DEFAULT = "true"
FALSE_VALUES = frozenset({"0", "false", "no", "off"})


def auto_prompt_value_enabled(value: str | None) -> bool:
    """Interpret a prompt setting using the established false-value semantics."""
    if value is None:
        return True
    return value.strip().lower() not in FALSE_VALUES


def resolve_auto_prompt_value(
    home: str | Path | None = None,
    *,
    environment: Mapping[str, str] | None = None,
) -> str:
    """Return the effective raw auto-prompt setting for one selected home.

    A process setting has priority.  Without it, only
    ``envs/ChatArch/.env`` under the selected ChatArch home is consulted.
    """
    source_environment = os.environ if environment is None else environment
    process_value = source_environment.get(AUTO_PROMPT_ENV_VAR)
    if process_value is not None:
        return process_value

    paths = get_paths(home)
    profile_value = EnvStore(paths.envs_dir).load_active(ChatArchConfig).get(
        AUTO_PROMPT_ENV_VAR
    )
    return AUTO_PROMPT_DEFAULT if profile_value is None else profile_value


def resolve_auto_prompt_enabled(
    home: str | Path | None = None,
    *,
    environment: Mapping[str, str] | None = None,
) -> bool:
    """Resolve process, active-profile, then default prompt policy."""
    return auto_prompt_value_enabled(
        resolve_auto_prompt_value(home, environment=environment)
    )


def auto_prompt_enabled(
    home: str | Path | None = None,
    *,
    environment: Mapping[str, str] | None = None,
) -> bool:
    """Compatibility-friendly name for :func:`resolve_auto_prompt_enabled`."""
    return resolve_auto_prompt_enabled(home, environment=environment)


__all__ = [
    "AUTO_PROMPT_DEFAULT",
    "AUTO_PROMPT_ENV_VAR",
    "FALSE_VALUES",
    "auto_prompt_enabled",
    "auto_prompt_value_enabled",
    "resolve_auto_prompt_enabled",
    "resolve_auto_prompt_value",
]
