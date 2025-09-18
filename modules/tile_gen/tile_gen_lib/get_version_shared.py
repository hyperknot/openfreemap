"""
This file is shared / symlinked between tile_gen_lib and http_host_lib
"""

from datetime import datetime, timezone

import requests


def get_versions_for_area(area: str) -> list:
    """
    Download the files.txt and check for the runs with the "done" file present
    """
    r = requests.get('https://btrfs.openfreemap.com/files.txt', timeout=30)
    r.raise_for_status()

    versions = []

    files = r.text.splitlines()
    for f in files:
        if not f.startswith(f'areas/{area}/'):
            continue
        if not f.endswith('/done'):
            continue
        version_str = f.split('/')[2]
        versions.append(version_str)

    return sorted(versions)


def get_deployed_version(area: str) -> dict:
    r = requests.get(f'https://assets.openfreemap.com/deployed_versions/{area}.txt', timeout=30)
    r.raise_for_status()
    version = r.text.strip()

    last_modified_str = r.headers.get('Last-Modified')
    last_modified = parse_http_last_modified(last_modified_str)

    return dict(
        version=version,
        last_modified=last_modified,
    )


def parse_http_last_modified(date_string) -> datetime:
    parsed_date = datetime.strptime(date_string, '%a, %d %b %Y %H:%M:%S GMT')
    parsed_date = parsed_date.replace(tzinfo=timezone.utc)
    return parsed_date
