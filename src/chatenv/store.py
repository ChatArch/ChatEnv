from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

from .fields import BaseEnvConfig, normalize_profile_name


class EnvStore:
    def __init__(self, envs_dir: str | Path):
        self.envs_dir = Path(envs_dir)

    def ensure_root(self) -> None:
        self.envs_dir.mkdir(parents=True, exist_ok=True)

    def config_dir(self, config_cls: type[BaseEnvConfig]) -> Path:
        return config_cls.get_storage_dir(self.envs_dir)

    def active_path(self, config_cls: type[BaseEnvConfig]) -> Path:
        return config_cls.get_active_env_file(self.envs_dir)

    def profile_path(self, config_cls: type[BaseEnvConfig], name: str) -> Path:
        return config_cls.get_profile_env_file(self.envs_dir, name)

    def list_profiles(self, config_cls: type[BaseEnvConfig]) -> list[str]:
        config_dir = self.config_dir(config_cls)
        if not config_dir.exists():
            return []
        return sorted(path.stem for path in config_dir.glob("*.env") if path.name != ".env")

    def load_active(self, config_cls: type[BaseEnvConfig]) -> dict[str, str]:
        return self.load_path(self.active_path(config_cls))

    def load_profile(self, config_cls: type[BaseEnvConfig], name: str) -> dict[str, str]:
        return self.load_path(self.profile_path(config_cls, name))

    def load_path(self, path: str | Path) -> dict[str, str]:
        file_path = Path(path)
        if not file_path.exists():
            return {}
        return {key: value for key, value in dotenv_values(file_path).items() if value is not None}

    def save_active(self, config_cls: type[BaseEnvConfig], values: dict[str, Any] | None = None) -> Path:
        return self._save(config_cls, self.active_path(config_cls), values)

    def save_profile(self, config_cls: type[BaseEnvConfig], name: str, values: dict[str, Any] | None = None) -> Path:
        normalize_profile_name(name)
        return self._save(config_cls, self.profile_path(config_cls, name), values)

    def use_profile(self, config_cls: type[BaseEnvConfig], name: str) -> Path:
        source = self.profile_path(config_cls, name)
        if not source.exists():
            raise FileNotFoundError(source)
        target = self.active_path(config_cls)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(source, target)
        return source

    def delete_profile(self, config_cls: type[BaseEnvConfig], name: str) -> Path:
        target = self.profile_path(config_cls, name)
        if not target.exists():
            raise FileNotFoundError(target)
        target.unlink()
        return target

    def _save(
        self,
        config_cls: type[BaseEnvConfig],
        target_path: Path,
        values: dict[str, Any] | None = None,
    ) -> Path:
        if values is not None:
            config_cls.load_from_sources(env_values=values)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(config_cls.render_env_file(), encoding="utf-8")
        return target_path
