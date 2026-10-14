from __future__ import annotations


def mask_secret(value: object, *, visible: int = 0) -> str:
    """Fully hide values by default; fingerprints require explicit opt-in."""
    text = "" if value is None else str(value)
    if not text:
        return ""
    if visible <= 0 or len(text) <= visible * 2:
        return "*" * len(text)
    return f"{text[:visible]}{'*' * (len(text) - visible * 2)}{text[-visible:]}"
