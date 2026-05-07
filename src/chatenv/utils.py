from __future__ import annotations


def mask_secret(value: object, *, visible: int = 8) -> str:
    text = "" if value is None else str(value)
    if not text:
        return ""
    if len(text) <= visible * 2:
        return "*" * len(text)
    return f"{text[:visible]}{'*' * (len(text) - visible * 2)}{text[-visible:]}"
