from __future__ import annotations

import os
from pathlib import Path
from typing import Any, ClassVar

from dotenv import dotenv_values

from .utils import mask_secret


class EnvField:
    """Descriptor-like metadata for one environment variable."""

    def __init__(
        self,
        env_key: str,
        default: Any = None,
        desc: str = "",
        is_sensitive: bool = False,
        sensitive: bool | None = None,
    ):
        self.env_key = env_key
        self.default = default
        self.desc = desc
        self.is_sensitive = is_sensitive if sensitive is None else sensitive
        self.value = default

    def __repr__(self) -> str:
        return f"EnvField(key={self.env_key!r}, default={self.default!r})"

    def mask_value(self) -> str:
        value = "" if self.value is None else str(self.value)
        return mask_secret(value) if self.is_sensitive else value


class BaseEnvConfig:
    """Base class for typed env/profile schemas."""

    _registry: ClassVar[list[type["BaseEnvConfig"]]] = []
    _registry_keys: ClassVar[dict[str, type["BaseEnvConfig"]]] = {}
    _title: ClassVar[str] = "Configuration"
    _aliases: ClassVar[list[str]] = []
    _storage_dir: ClassVar[str | None] = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls in BaseEnvConfig._registry:
            return
        registry_key = cls.get_registry_key()
        existing = BaseEnvConfig._registry_keys.get(registry_key)
        if existing is not None:
            setattr(cls, "_duplicate_of", existing)
            return
        BaseEnvConfig._registry.append(cls)
        BaseEnvConfig._registry_keys[registry_key] = cls

    @classmethod
    def get_registry_key(cls) -> str:
        """Return the logical registry key used for duplicate detection."""
        return cls.get_storage_name().strip().lower()

    @classmethod
    def get_fields(cls) -> dict[str, EnvField]:
        return {
            name: value
            for name, value in cls.__dict__.items()
            if isinstance(value, EnvField)
        }

    @classmethod
    def get_storage_name(cls) -> str:
        return cls._storage_dir or cls.__name__.removesuffix("Config") or cls.__name__

    @classmethod
    def get_storage_dir(cls, env_root: str | Path) -> Path:
        return Path(env_root) / cls.get_storage_name()

    @classmethod
    def get_active_env_file(cls, env_root: str | Path) -> Path:
        return cls.get_storage_dir(env_root) / ".env"

    @classmethod
    def get_profile_env_file(cls, env_root: str | Path, name: str) -> Path:
        profile_name = normalize_profile_name(name)
        return cls.get_storage_dir(env_root) / f"{profile_name}.env"

    @classmethod
    def render_env_file(cls) -> str:
        lines = [f"# Description: Env file for {cls._title}.", ""]
        for field in cls.get_fields().values():
            if field.desc:
                lines.append(f"# {field.desc}")
            value = "" if field.value is None else str(field.value)
            lines.append(f"{field.env_key}='{value}'")
            lines.append("")
        return "\n".join(lines)

    @classmethod
    def load_from_dict(cls, env_values: dict[str, Any]) -> None:
        cls.load_from_sources(env_values=env_values)

    @classmethod
    def load_from_sources(
        cls,
        env_values: dict[str, Any] | None = None,
        override_values: dict[str, Any] | None = None,
    ) -> None:
        env_values = env_values or {}
        override_values = override_values or {}
        for field in cls.get_fields().values():
            value = override_values.get(field.env_key)
            if value is None:
                value = env_values.get(field.env_key)
            if value is None:
                value = os.getenv(field.env_key)
            field.value = field.default if value is None else value

    @classmethod
    def _read_env_values(cls, env_file: str | Path | None) -> dict[str, str]:
        if env_file is None:
            return {}
        path = Path(env_file)
        if not path.exists() or not path.is_file():
            return {}
        return {key: value for key, value in dotenv_values(path).items() if value is not None}

    @classmethod
    def _load_base_values(
        cls,
        env_path: str | Path | None,
        legacy_env_file: str | Path | None = None,
    ) -> dict[type["BaseEnvConfig"], dict[str, str]]:
        if env_path is None:
            return {config_cls: {} for config_cls in cls._registry}

        source_path = Path(env_path)
        if source_path.is_file():
            env_values = cls._read_env_values(source_path)
            return {config_cls: env_values for config_cls in cls._registry}

        legacy_values = cls._read_env_values(legacy_env_file)
        values_by_config: dict[type[BaseEnvConfig], dict[str, str]] = {}
        for config_cls in cls._registry:
            config_path = config_cls.get_active_env_file(source_path)
            values_by_config[config_cls] = (
                cls._read_env_values(config_path) if config_path.exists() else legacy_values
            )
        return values_by_config

    @classmethod
    def load_all(
        cls,
        env_path: str | Path | None,
        legacy_env_file: str | Path | None = None,
    ) -> None:
        base_values = cls._load_base_values(env_path, legacy_env_file=legacy_env_file)
        for config_cls in cls._registry:
            config_cls.load_from_sources(env_values=base_values.get(config_cls, {}))

    @classmethod
    def load_all_with_override(
        cls,
        env_path: str | Path | None,
        override_env_file: str | Path,
        legacy_env_file: str | Path | None = None,
    ) -> None:
        base_values = cls._load_base_values(env_path, legacy_env_file=legacy_env_file)
        override_values = cls._read_env_values(override_env_file)
        for config_cls in cls._registry:
            config_cls.load_from_sources(
                env_values=base_values.get(config_cls, {}),
                override_values=override_values,
            )

    @classmethod
    def get_all_values(cls) -> dict[str, Any]:
        values: dict[str, Any] = {}
        for config_cls in cls._registry:
            for name, field in config_cls.get_fields().items():
                values[name] = field.value
        return values

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        match = cls.find_field(key)
        if match is not None:
            _, field = match
            field.value = value

    @classmethod
    def find_field(cls, key: str) -> tuple[type["BaseEnvConfig"], EnvField] | None:
        normalized = key.strip().lower()
        for config_cls in cls._registry:
            for name, field in config_cls.get_fields().items():
                if name.lower() == normalized or field.env_key.lower() == normalized:
                    return config_cls, field
        return None

    @classmethod
    def generate_env_template(cls, current_version: str = "") -> str:
        lines = ["# Description: Env file for ChatArch."]
        if current_version:
            lines.append(f"# Current version: {current_version}")
        lines.append("")
        for config_cls in cls._registry:
            lines.append(f"# ==================== {config_cls._title} ====================")
            for field in config_cls.get_fields().values():
                if field.desc:
                    lines.append(f"# {field.desc}")
                value = "" if field.value is None else str(field.value)
                lines.append(f"{field.env_key}='{value}'")
                lines.append("")
        return "\n".join(lines)

    @classmethod
    def get_config_by_alias(cls, alias: str) -> type["BaseEnvConfig"] | None:
        normalized = alias.strip().lower()
        for config_cls in cls._registry:
            aliases = [item.lower() for item in getattr(config_cls, "_aliases", [])]
            if normalized in aliases or normalized == config_cls.get_storage_name().lower():
                return config_cls
        return None

    @classmethod
    def test(cls) -> None:
        print(f"Testing {cls._title}...")
        raise NotImplementedError("Test method not implemented for this configuration.")

    @classmethod
    def save_env_file(cls, env_path: str | Path, version: str = "0.0.0") -> None:
        path = Path(env_path)
        if path.suffix == ".env":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(cls.generate_env_template(version), encoding="utf-8")
            return

        path.mkdir(parents=True, exist_ok=True)
        for config_cls in cls._registry:
            config_dir = config_cls.get_storage_dir(path)
            config_dir.mkdir(parents=True, exist_ok=True)
            config_cls.get_active_env_file(path).write_text(
                config_cls.render_env_file(),
                encoding="utf-8",
            )

    @classmethod
    def print_config(cls) -> None:
        for config_cls in cls._registry:
            print(f"\n{config_cls._title}:")
            for name, field in config_cls.get_fields().items():
                if not field.value:
                    continue
                shown = field.mask_value() if field.is_sensitive else field.value
                print(f"  {name}: {shown}")


def normalize_profile_name(name: str) -> str:
    profile_name = str(name).strip()
    if not profile_name:
        raise ValueError("Profile name cannot be empty.")
    return profile_name.removesuffix(".env")
