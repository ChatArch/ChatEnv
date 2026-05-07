from __future__ import annotations

import os
import traceback
from dataclasses import dataclass
from importlib.metadata import EntryPoint, entry_points
from typing import Iterable

import click

from .fields import BaseEnvConfig


ENTRY_POINT_GROUP = "chatenv.configs"
_loaded = False
_provider_configs: dict[str, list[type[BaseEnvConfig]]] = {}
_provider_errors: dict[str, Exception] = {}


@dataclass(frozen=True)
class ProviderLoadResult:
    name: str
    value: str
    loaded: bool
    configs: tuple[type[BaseEnvConfig], ...] = ()
    error: Exception | None = None


def _iter_entry_points() -> Iterable[EntryPoint]:
    eps = entry_points()
    if hasattr(eps, "select"):
        return eps.select(group=ENTRY_POINT_GROUP)
    return eps.get(ENTRY_POINT_GROUP, [])


def load_config_providers(*, force: bool = False, debug: bool | None = None) -> list[ProviderLoadResult]:
    """Load installed config providers registered through entry points."""
    global _loaded
    if _loaded and not force:
        return []

    _loaded = True
    debug = debug if debug is not None else os.getenv("CHATENV_DEBUG") == "1"
    results: list[ProviderLoadResult] = []

    for ep in _iter_entry_points():
        before = set(BaseEnvConfig._registry)
        try:
            ep.load()
        except Exception as exc:  # pragma: no cover - exact provider failures vary
            _provider_errors[ep.name] = exc
            results.append(
                ProviderLoadResult(ep.name, ep.value, loaded=False, error=exc)
            )
            message = f"Warning: failed to load chatenv provider {ep.name}: {exc}"
            click.echo(message, err=True)
            if debug:
                traceback.print_exception(type(exc), exc, exc.__traceback__)
            continue

        after = [config_cls for config_cls in BaseEnvConfig._registry if config_cls not in before]
        for config_cls in after:
            setattr(config_cls, "_provider", ep.name)
        _provider_configs.setdefault(ep.name, []).extend(after)
        results.append(
            ProviderLoadResult(ep.name, ep.value, loaded=True, configs=tuple(after))
        )

    return results


def get_provider_configs() -> dict[str, list[type[BaseEnvConfig]]]:
    return {name: list(configs) for name, configs in _provider_configs.items()}


def get_provider_errors() -> dict[str, Exception]:
    return dict(_provider_errors)
