import re
import unicodedata


# Pre-compiled patterns for better performance
_RE_INVALID = re.compile(r'[^a-z0-9_-]+')
_RE_SEPARATORS = re.compile(r'[-_]+')


def slugify(
    value: str | bytes | int | float | None,
    *,
    separator: str = '-',
) -> str:
    if value in (None, ''):
        return ''

    if separator not in ('-', '_'):
        raise ValueError(f"separator must be '-' or '_', got {repr(separator)}")

    # 1. Normalize value to string
    if isinstance(value, bytes):
        value = value.decode('utf-8', 'ignore')
    else:
        value = str(value)

    # 2. Unicode → ASCII, then lowercase
    value = unicodedata.normalize('NFKD', value)
    value = value.encode('ascii', 'ignore').decode('ascii').lower()

    # 3. Replace invalid characters with separator
    value = _RE_INVALID.sub(separator, value)

    # 4. Collapse multiple separators
    value = _RE_SEPARATORS.sub(separator, value)

    # 5. Strip separators from edges
    value = value.strip('-_')

    return value
