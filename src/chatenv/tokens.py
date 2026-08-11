"""Generic runtime token store for ChatArch tools.

ChatEnv owns only the generic management substrate. It stores one runtime
state document per service/profile under ``$CHATARCH_HOME/tokens`` and never
interprets service-specific token semantics.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .paths import get_paths

TOKEN_SCHEMA_VERSION = 1
DEFAULT_PROFILE = "default"
DEFAULT_TOKEN_TYPE = "runtime"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_segment(value: str, *, default: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value or "").strip())
    cleaned = cleaned.strip(".-")
    return cleaned or default


def _strict_token_profile_segment(value: str | None) -> str:
    if value is None:
        return DEFAULT_PROFILE
    raw = str(value)
    stripped = raw.strip()
    if not stripped:
        raise ValueError("token profile must not be empty")
    if stripped != raw:
        raise ValueError("token profile must not contain leading or trailing whitespace")
    if stripped in {".", ".."}:
        raise ValueError("token profile must not be '.' or '..'")
    if "/" in stripped or "\\" in stripped:
        raise ValueError("token profile must be a single path segment")
    if re.search(r"[^A-Za-z0-9_.-]", stripped):
        raise ValueError("token profile may contain only letters, numbers, dot, underscore, and hyphen")
    if stripped.strip(".-") != stripped:
        raise ValueError("token profile must not start or end with dot or hyphen")
    return stripped


def normalize_service_name(value: str) -> str:
    return _safe_segment(value, default="Service")


def normalize_token_profile(value: str | None) -> str:
    return _strict_token_profile_segment(value)


def _coerce_mapping(value: dict[str, Any] | None) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


class TokenStore:
    """Generic JSON token store keyed by service/profile.

    The ``values`` object is opaque and may contain secrets. ``status`` and
    ``list_tokens`` intentionally expose only safe metadata and caller-supplied
    summary fields.
    """

    def __init__(self, *, home: str | Path | None = None, tokens_dir: str | Path | None = None):
        self.tokens_dir = Path(tokens_dir) if tokens_dir is not None else get_paths(home).tokens_dir

    def token_path(self, service: str, profile: str | None = None) -> Path:
        service_name = normalize_service_name(service)
        profile_name = normalize_token_profile(profile)
        return self.tokens_dir / service_name / f"{profile_name}.json"

    def read(self, service: str, profile: str | None = None) -> dict[str, Any]:
        path = self.token_path(service, profile)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except (OSError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def write(
        self,
        service: str,
        profile: str | None = None,
        *,
        values: dict[str, Any],
        token_type: str = DEFAULT_TOKEN_TYPE,
        summary: dict[str, Any] | None = None,
        expires_at: str | None = None,
        source: str = "refresh",
    ) -> dict[str, Any]:
        if not isinstance(values, dict) or not values:
            raise ValueError("values must be a non-empty JSON object")
        service_name = normalize_service_name(service)
        profile_name = normalize_token_profile(profile)
        path = self.token_path(service_name, profile_name)
        existing = self.read(service_name, profile_name)
        now = _iso(_now())
        payload = {
            "schema_version": TOKEN_SCHEMA_VERSION,
            "service": service_name,
            "profile": profile_name,
            "token_type": token_type or DEFAULT_TOKEN_TYPE,
            "created_at": existing.get("created_at") or now,
            "updated_at": now,
            "expires_at": expires_at or "",
            "source": source,
            "summary": _coerce_mapping(summary),
            "values": values,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent), text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.write("\n")
            os.replace(tmp_name, path)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
        return self.status(service_name, profile_name)

    def status(self, service: str, profile: str | None = None) -> dict[str, Any]:
        service_name = normalize_service_name(service)
        profile_name = normalize_token_profile(profile)
        path = self.token_path(service_name, profile_name)
        payload = self.read(service_name, profile_name)
        values = payload.get("values") if isinstance(payload, dict) else None
        token_present = isinstance(values, dict) and bool(values)
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        return {
            "ok": True,
            "service": service_name,
            "profile": profile_name,
            "token_type": payload.get("token_type") or DEFAULT_TOKEN_TYPE,
            "token_file": str(path),
            "token_file_exists": path.exists(),
            "token_present": token_present,
            "created_at": payload.get("created_at") or "",
            "updated_at": payload.get("updated_at") or "",
            "expires_at": payload.get("expires_at") or "",
            "source": payload.get("source") or "",
            "summary": summary,
        }

    def list_tokens(self, service: str | None = None) -> list[dict[str, Any]]:
        roots: list[Path]
        if service:
            roots = [self.tokens_dir / normalize_service_name(service)]
        elif self.tokens_dir.exists():
            roots = sorted(path for path in self.tokens_dir.iterdir() if path.is_dir())
        else:
            roots = []
        items: list[dict[str, Any]] = []
        for root in roots:
            for path in sorted(root.glob("*.json")):
                items.append(self.status(root.name, path.stem))
        return sorted(items, key=lambda item: (str(item["service"]), str(item["profile"])))

    def clear(self, service: str, profile: str | None = None, *, execute: bool = False) -> dict[str, Any]:
        service_name = normalize_service_name(service)
        profile_name = normalize_token_profile(profile)
        path = self.token_path(service_name, profile_name)
        exists = path.exists()
        if not execute:
            return {
                "ok": True,
                "mutated": False,
                "service": service_name,
                "profile": profile_name,
                "token_file": str(path),
                "token_file_exists": exists,
                "would_delete": str(path),
            }
        if exists:
            path.unlink()
        return {
            "ok": True,
            "mutated": exists,
            "service": service_name,
            "profile": profile_name,
            "token_file": str(path),
            "token_file_exists": False,
            "deleted": exists,
        }


__all__ = [
    "DEFAULT_PROFILE",
    "DEFAULT_TOKEN_TYPE",
    "TOKEN_SCHEMA_VERSION",
    "TokenStore",
    "normalize_service_name",
    "normalize_token_profile",
]
