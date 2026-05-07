from __future__ import annotations

from .fields import BaseEnvConfig


def resolve_config_types(config_types: tuple[str, ...] | list[str] | None) -> list[type[BaseEnvConfig]] | None:
    if not config_types:
        return None
    normalized = [item.lower() for item in config_types]
    matched: list[type[BaseEnvConfig]] = []
    for config_cls in BaseEnvConfig._registry:
        title = getattr(config_cls, "_title", config_cls.__name__).lower()
        aliases = [alias.lower() for alias in getattr(config_cls, "_aliases", [])]
        storage_name = config_cls.get_storage_name().lower()
        for item in normalized:
            if title.startswith(item) or storage_name.startswith(item):
                matched.append(config_cls)
                break
            if any(alias.startswith(item) for alias in aliases):
                matched.append(config_cls)
                break
    return matched


def require_single_config(config_types: tuple[str, ...] | list[str] | None, action: str) -> type[BaseEnvConfig]:
    if not config_types:
        raise ValueError(f"{action} requires --type/-t to select exactly one config type.")
    matched = resolve_config_types(config_types) or []
    if len(matched) != 1:
        names = ", ".join(config_cls.get_storage_name() for config_cls in matched) or "none"
        raise ValueError(f"{action} requires exactly one config type. Matched: {names}")
    return matched[0]
