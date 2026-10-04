import os
import subprocess
import sys
from pathlib import Path

import requests

from shared_lib.utils.cloudflare import CloudflareError


def assert_sudo():
    if os.geteuid() != 0:
        sys.exit('  needs sudo')


def assert_linux():
    if not sys.platform.startswith('linux'):
        sys.exit('  needs to be run on Linux')


def get_remote_file_size(url: str) -> int:
    r = requests.head(url, timeout=30)
    r.raise_for_status()
    size = r.headers.get('Content-Length')
    if not size:
        raise CloudflareError(f'missing Content-Length for {url}')
    return int(size)


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
    code = subprocess.run(args).returncode
    # Local, not Cloudflare: negative = killed by a signal (e.g. OOM); 9, 13-18: disk
    # full, file exists, rename, open/create/IO, mkdir; 28: bad option (code/aria2 version)
    if code < 0 or code in {9, 13, 14, 15, 16, 17, 18, 28}:
        raise RuntimeError(f'aria2c exit {code} for {url}')
    if code != 0:
        raise CloudflareError(f'aria2c exit {code} for {url}')
