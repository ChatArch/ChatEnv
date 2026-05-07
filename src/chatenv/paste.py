from __future__ import annotations

import re
from dataclasses import dataclass, field

from .fields import BaseEnvConfig, EnvField

_ENV_ASSIGN_RE = re.compile(r"(?:^|[^A-Za-z0-9_])(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=")


@dataclass
class PasteResult:
    grouped: dict[type[BaseEnvConfig], dict[str, str]] = field(default_factory=dict)
    unknown: list[str] = field(default_factory=list)

    @property
    def recognized_count(self) -> int:
        return sum(len(values) for values in self.grouped.values())


def unquote_pasted_value(raw_value: str) -> str:
    value = raw_value.strip()
    if not value:
        return ""
    quote = value[0]
    if quote in ("'", '"'):
        chars: list[str] = []
        escaped = False
        for char in value[1:]:
            if escaped:
                chars.append(char)
                escaped = False
                continue
            if quote == '"' and char == "\\":
                escaped = True
                continue
            if char == quote:
                return "".join(chars)
            chars.append(char)
        return "".join(chars)
    if " #" in value:
        value = value.split(" #", 1)[0].rstrip()
    return value


def extract_pasted_assignment(line: str) -> tuple[str, str] | None:
    match = _ENV_ASSIGN_RE.search(line)
    if match is None:
        return None
    key = match.group(1)
    return key, unquote_pasted_value(line[match.end():])


def parse_pasted_env_text(text: str) -> PasteResult:
    result = PasteResult()
    for line in text.splitlines():
        parsed = extract_pasted_assignment(line)
        if parsed is None:
            continue
        key, value = parsed
        match = BaseEnvConfig.find_field(key)
        if match is None:
            result.unknown.append(key)
            continue
        config_cls, field = match
        result.grouped.setdefault(config_cls, {})[field.env_key] = value
    return result


def iter_fields_for_values(config_cls: type[BaseEnvConfig], values: dict[str, str]):
    fields_by_key: dict[str, EnvField] = {field.env_key: field for field in config_cls.get_fields().values()}
    for key, value in values.items():
        field = fields_by_key.get(key)
        if field is not None:
            yield field, value
