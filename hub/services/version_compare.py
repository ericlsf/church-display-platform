"""Canonical version comparison for display releases."""


def canonical_version(value):
    text = str(value or "").strip()

    if not text:
        return ""

    if text.lower().startswith("version "):
        text = text[8:].strip()

    if text[:1].lower() == "v":
        text = text[1:]

    return text.strip()


def versions_match(left, right):
    left_value = canonical_version(left)
    right_value = canonical_version(right)

    return bool(
        left_value
        and right_value
        and left_value == right_value
    )
