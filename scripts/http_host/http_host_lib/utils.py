import os
import subprocess
import sys
import time
from pathlib import Path

import requests


def assert_sudo():
    if os.geteuid() != 0:
        sys.exit('  needs sudo')


def assert_linux():
    if not Path('/etc/fstab').exists():
        sys.exit('  needs to be run on Linux')


def assert_single_process():
    p = subprocess.run(['pgrep', '-fl', sys.argv[0]], capture_output=True, text=True)
    lines = [l for l in p.stdout.splitlines() if 'python' in l]
    if len(lines) >= 2:
        sys.exit('  detected multiple processes, terminating')


def download_if_size_differs(url: str, local_file: Path) -> bool:
    if not local_file.exists() or local_file.stat().st_size != get_remote_file_size(url):
        download_file_aria2(url, local_file)
        return True

    return False


def get_remote_file_size(url: str) -> int | None:
    r = requests.head(url)
    size = r.headers.get('Content-Length')
    return int(size) if size else None


def download_file_aria2(url: str, local_file: Path):
    print(f'  downloading: {url} into {local_file}')

    subprocess.run(
        [
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
        ],
        check=True,
    )
