"""Shared version helpers for tilegen and linux_host."""

import re

import requests

from shared_lib.utils.cloudflare import CloudflareError


def get_versions_by_area(areas: list[str]) -> dict[str, list[str]]:
    """
    Download the files.txt and check for the runs with the "done" file present
    """
    r = requests.get('https://btrfs.openfreemap.com/files.txt', timeout=30)
    r.raise_for_status()

    versions: dict[str, list[str]] = {area: [] for area in areas}
    for f in r.text.splitlines():
        parts = f.split('/')
        if len(parts) == 4 and parts[0] == 'areas' and parts[1] in versions and parts[3] == 'done':
            versions[parts[1]].append(parts[2])

    for area, area_versions in versions.items():
        if not area_versions:
            raise CloudflareError(f'no finished versions in files.txt for {area}')
        area_versions.sort()

    return versions


def get_deployed_version(area: str) -> str:
    r = requests.get(f'https://assets.openfreemap.com/deployed_versions/{area}.txt', timeout=30)
    r.raise_for_status()
    version = r.text.strip()
    if not re.fullmatch(r'\d{8}_\d{6}_pt', version):
        raise CloudflareError(f'invalid deployed version for {area}: {version[:50]!r}')
    return version
