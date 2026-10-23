import os
import re
from email.utils import formatdate, parsedate_to_datetime
from pathlib import Path

import requests


# Outside /data/ofm, so --reinstall keeps it.
WATER_POLYGONS_PATH = Path('/data/ofm_keep/sources/water-polygons-split-3857.zip')

OSMDATA_URL = 'https://osmdata.openstreetmap.de/download/water-polygons-split-3857.zip'
FAU_ARCHIVE_URL = 'https://ftp.fau.de/mirrors/openstreetmapdata.com-archive/'

# ValueError: max() on an empty FAU listing, if its format changes
DOWNLOAD_ERRORS = (requests.RequestException, OSError, ValueError)


def ensure_water_polygons(refresh: bool) -> None:
    """
    Keep a persistent copy of the water polygons, so Planetiler doesn't download them on every run.
    Downloads when missing or when refresh is set: osmdata first, FAU mirror as fallback.
    If both fail, keeps using the existing copy. This is only logged, so if both sources break
    for good, the copy silently gets older.
    """

    path = WATER_POLYGONS_PATH
    if path.exists() and not refresh:
        return

    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        _download_if_modified(OSMDATA_URL, path)
        return
    except DOWNLOAD_ERRORS as e:
        print(f'water polygons: osmdata failed: {e}')

    try:
        _download_if_modified(_latest_fau_url(), path)
        return
    except DOWNLOAD_ERRORS as e:
        print(f'water polygons: FAU mirror failed: {e}')

    if not path.exists():
        raise RuntimeError('water polygons: all sources failed and no existing copy')

    print(f'water polygons: using existing copy {path}')


def _download_if_modified(url: str, path: Path) -> None:
    headers = {}
    if path.exists():
        headers['If-Modified-Since'] = formatdate(path.stat().st_mtime, usegmt=True)

    print(f'water polygons: checking {url}')
    tmp_path = path.with_name(path.name + '.tmp')
    with requests.get(url, headers=headers, stream=True, timeout=60) as r:
        if r.status_code == 304:
            print('water polygons: not modified')
            return
        r.raise_for_status()

        print('water polygons: downloading')
        with tmp_path.open('wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)

    # keep the server's modification time, so the next If-Modified-Since compares correctly
    if last_modified := r.headers.get('Last-Modified'):
        mtime = parsedate_to_datetime(last_modified).timestamp()
        os.utime(tmp_path, (mtime, mtime))

    tmp_path.replace(path)
    print('water polygons: download DONE')


def _latest_fau_url() -> str:
    r = requests.get(FAU_ARCHIVE_URL, timeout=60)
    r.raise_for_status()
    dates = re.findall(r'href="(\d{4}-\d{2}-\d{2})/"', r.text)
    return f'{FAU_ARCHIVE_URL}{max(dates)}/water-polygons-split-3857.zip'
