from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ChatArchPaths:
    home_dir: Path

    @property
    def envs_dir(self) -> Path:
        return self.home_dir / "envs"


def _expand_path(value: str | Path) -> Path:
    return Path(value).expanduser().resolve()


def get_paths(home: str | Path | None = None) -> ChatArchPaths:
    raw_home = home or os.getenv("CHATARCH_HOME") or "~/.chatarch"
    return ChatArchPaths(home_dir=_expand_path(raw_home))
