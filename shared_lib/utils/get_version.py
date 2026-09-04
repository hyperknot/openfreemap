"""Shared version helpers for tilegen and linux_host."""

from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any

import requests


def get_versions_for_area(area: str) -> list[str]:
    """
    Download the files.txt and check for the runs with the "done" file present
    """
    r = requests.get('https://btrfs.openfreemap.com/files.txt', timeout=30)
    r.raise_for_status()

    versions: list[str] = []

    files = r.text.splitlines()
    for f in files:
        if not f.startswith(f'areas/{area}/'):
            continue
        if not f.endswith('/done'):
            continue
        version_str = f.split('/')[2]
        versions.append(version_str)

    return sorted(versions)


def get_deployed_version(area: str) -> dict[str, Any]:
    r = requests.get(f'https://assets.openfreemap.com/deployed_versions/{area}.txt', timeout=30)
    r.raise_for_status()
    version = r.text.strip()

    last_modified_str = r.headers.get('Last-Modified')
    last_modified = parse_http_last_modified(last_modified_str)

    return dict(
        version=version,
        last_modified=last_modified,
    )


def parse_http_last_modified(date_string: str | None) -> datetime:
    if date_string is None:
        raise ValueError('Last-Modified header is missing')
    return parsedate_to_datetime(date_string)
