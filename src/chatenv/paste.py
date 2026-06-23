from __future__ import annotations

import re
from dataclasses import dataclass, field

from .fields import BaseEnvConfig, EnvField

_ENV_ASSIGN_RE = re.compile(r"(?:^|[^A-Za-z0-9_])(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=")
_SPACED_ENV_ASSIGN_RE = re.compile(r"(?:^|\s)(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=")


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


def _comment_index(value: str) -> int | None:
    index = value.find(" #")
    return index if index >= 0 else None


def _quoted_value_end(line: str, value_start: int, quote: str) -> int:
    escaped = False
    for index in range(value_start + 1, len(line)):
        char = line[index]
        if escaped:
            escaped = False
            continue
        if quote == '"' and char == "\\":
            escaped = True
            continue
        if char == quote:
            return index + 1
    return len(line)


def _next_assignment_match(line: str, start: int):
    return _SPACED_ENV_ASSIGN_RE.search(line, start)


def _parse_value_and_next_position(line: str, value_start: int) -> tuple[str, int]:
    stripped_start = value_start
    while stripped_start < len(line) and line[stripped_start].isspace():
        stripped_start += 1

    if stripped_start >= len(line):
        return "", len(line)

    quote = line[stripped_start]
    if quote in ("'", '"'):
        value_end = _quoted_value_end(line, stripped_start, quote)
        next_match = _next_assignment_match(line, value_end)
        if next_match is None:
            next_pos = len(line)
        else:
            between = line[value_end:next_match.start()]
            next_pos = len(line) if _comment_index(between) is not None else next_match.start()
        return unquote_pasted_value(line[value_start:value_end]), next_pos

    next_match = _next_assignment_match(line, value_start)
    if next_match is None:
        return unquote_pasted_value(line[value_start:]), len(line)

    segment = line[value_start:next_match.start()]
    comment = _comment_index(segment)
    if comment is not None:
        return unquote_pasted_value(segment[:comment]), len(line)
    return unquote_pasted_value(segment), next_match.start()


def iter_pasted_assignments(line: str):
    position = 0
    while True:
        match = _ENV_ASSIGN_RE.search(line, position)
        if match is None:
            break
        key = match.group(1)
        value, position = _parse_value_and_next_position(line, match.end())
        yield key, value
        if position >= len(line):
            break


def extract_pasted_assignment(line: str) -> tuple[str, str] | None:
    return next(iter_pasted_assignments(line), None)


def parse_pasted_env_text(text: str) -> PasteResult:
    result = PasteResult()
    for line in text.splitlines():
        for key, value in iter_pasted_assignments(line):
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
