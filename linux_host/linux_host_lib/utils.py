import os
import subprocess
import sys
from pathlib import Path

import requests


def assert_sudo():
    if os.geteuid() != 0:
        sys.exit('  needs sudo')


def assert_linux():
    if not sys.platform.startswith('linux'):
        sys.exit('  needs to be run on Linux')


def get_remote_file_size(url: str) -> int | None:
    r = requests.head(url, timeout=30)
    r.raise_for_status()
    size = r.headers.get('Content-Length')
    return int(size) if size else None


def download_file_aria2(url: str, local_file: Path) -> None:
    print(f'  downloading {url} into {local_file}')
    local_file.unlink(missing_ok=True)

    args = [
        'aria2c',
        '--split=8',
        '--max-connection-per-server=8',
        '--file-allocation=none',
        '--min-split-size=1M',
        '-d',
        local_file.parent,
        '-o',
        local_file.name,
        url,
    ]
    subprocess.run(args, check=True)
