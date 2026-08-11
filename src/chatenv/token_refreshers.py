"""Service-owned runtime token refresh hooks.

ChatEnv owns token-store persistence and safe metadata rendering. Service
packages own authentication semantics. A service can register a refresh
provider through the ``chatenv.token_refreshers`` entry-point group; ChatEnv
then invokes that provider for ``chatenv token refresh SERVICE PROFILE`` and
writes the returned opaque runtime values into ``tokens/<Service>/<profile>.json``.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import EntryPoint, entry_points
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from .paths import get_paths
from .store import EnvStore
from .tokens import DEFAULT_TOKEN_TYPE, TokenStore, normalize_service_name, normalize_token_profile

ENTRY_POINT_GROUP = "chatenv.token_refreshers"


@dataclass(frozen=True)
class TokenRefreshResult:
    """Opaque values plus safe metadata returned by a service refresh hook."""

    values: Mapping[str, Any]
    token_type: str = DEFAULT_TOKEN_TYPE
    summary: Mapping[str, Any] | None = None
    expires_at: str | None = None


_token_refreshers: dict[str, Callable[..., Any]] = {}
_loaded = False


def _iter_refresh_entry_points() -> Iterable[EntryPoint]:
    eps = entry_points()
    if hasattr(eps, "select"):
        return eps.select(group=ENTRY_POINT_GROUP)
    return eps.get(ENTRY_POINT_GROUP, [])


def clear_token_refreshers() -> None:
    """Clear the refresh-provider cache; intended for tests and reloads."""

    global _loaded
    _loaded = False
    _token_refreshers.clear()


def _provider_callable(obj: Any) -> Callable[..., Any]:
    if callable(obj):
        return obj
    for attr in ("refresh_token", "refresh"):
        candidate = getattr(obj, attr, None)
        if callable(candidate):
            return candidate
    raise TypeError("token refresh provider must be callable or expose refresh_token()/refresh()")


def load_token_refreshers(*, force: bool = False) -> dict[str, Callable[..., Any]]:
    """Load service refresh hooks registered through entry points."""

    global _loaded
    if _loaded and not force:
        return dict(_token_refreshers)
    if force:
        _token_refreshers.clear()
    _loaded = True
    for ep in _iter_refresh_entry_points():
        service_name = normalize_service_name(ep.name)
        provider = _provider_callable(ep.load())
        _token_refreshers[service_name.lower()] = provider
    return dict(_token_refreshers)


def get_token_refresher(service: str, *, force: bool = False) -> Callable[..., Any] | None:
    service_name = normalize_service_name(service)
    return load_token_refreshers(force=force).get(service_name.lower())


def _coerce_refresh_result(result: Any) -> TokenRefreshResult:
    if isinstance(result, TokenRefreshResult):
        return result
    if isinstance(result, Mapping):
        values = result.get("values")
        if not isinstance(values, Mapping):
            raise ValueError("token refresh provider result must include a non-empty values object")
        return TokenRefreshResult(
            values=values,
            token_type=str(result.get("token_type") or DEFAULT_TOKEN_TYPE),
            summary=result.get("summary") if isinstance(result.get("summary"), Mapping) else None,
            expires_at=str(result.get("expires_at") or ""),
        )
    raise ValueError("token refresh provider must return TokenRefreshResult or a mapping")


def refresh_token(
    service: str,
    profile: str | None = None,
    *,
    home: str | Path | None = None,
    env_store: EnvStore | None = None,
    token_store: TokenStore | None = None,
) -> dict[str, Any]:
    """Invoke the registered service refresh hook and persist its token values."""

    service_name = normalize_service_name(service)
    profile_name = normalize_token_profile(profile)
    provider = get_token_refresher(service_name)
    if provider is None:
        raise ValueError(f"No token refresh provider registered for {service_name}")

    paths = get_paths(home)
    env_store = env_store or EnvStore(paths.envs_dir)
    token_store = token_store or TokenStore(tokens_dir=paths.tokens_dir)
    result = _coerce_refresh_result(
        provider(
            service=service_name,
            profile=profile_name,
            home=paths.home_dir,
            env_store=env_store,
            token_store=token_store,
        )
    )
    return token_store.write(
        service_name,
        profile_name,
        values=dict(result.values),
        token_type=result.token_type or DEFAULT_TOKEN_TYPE,
        summary=dict(result.summary or {}),
        expires_at=result.expires_at or "",
        source="refresh",
    )


__all__ = [
    "ENTRY_POINT_GROUP",
    "TokenRefreshResult",
    "clear_token_refreshers",
    "get_token_refresher",
    "load_token_refreshers",
    "refresh_token",
]
