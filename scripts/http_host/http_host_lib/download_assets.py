import shutil
import subprocess
from pathlib import Path

import requests

from http_host_lib.utils import download_file_aria2, download_if_size_differs


def download_fonts(assets_dir: Path):
    """
    Download and extract font assets if their file size differ.
    """

    fonts_dir = assets_dir / 'fonts'
    fonts_dir.mkdir(exist_ok=True, parents=True)

    url = 'https://assets.openfreemap.com/fonts/ofm.tar.gz'
    local_file = fonts_dir / 'ofm.tar.gz'
    if not download_if_size_differs(url, local_file):
        return

    ofm_dir = fonts_dir / 'ofm'
    ofm_dir_bak = fonts_dir / 'ofm.bak'
    shutil.rmtree(ofm_dir_bak, ignore_errors=True)
    if ofm_dir.exists():
        ofm_dir.rename(ofm_dir_bak)

    subprocess.run(
        ['tar', '-xzf', local_file, '-C', fonts_dir],
        check=True,
    )


def download_styles(assets_dir: Path):
    """
    Download and extract style assets if their file size differ.
    """

    styles_dir = assets_dir / 'styles'
    styles_dir.mkdir(exist_ok=True, parents=True)

    url = 'https://assets.openfreemap.com/styles/ofm.tar.gz'
    local_file = styles_dir / 'ofm.tar.gz'
    if not download_if_size_differs(url, local_file):
        return

    ofm_dir = styles_dir / 'ofm'
    ofm_dir_bak = styles_dir / 'ofm.bak'
    shutil.rmtree(ofm_dir_bak, ignore_errors=True)
    if ofm_dir.exists():
        ofm_dir.rename(ofm_dir_bak)

    subprocess.run(
        ['tar', '-xzf', local_file, '-C', styles_dir],
        check=True,
    )


def download_sprites(assets_dir: Path):
    """
    Download and extract sprites if a version is not available locally
    """

    sprites_dir = assets_dir / 'sprites'
    sprites_dir.mkdir(exist_ok=True, parents=True)

    r = requests.get('https://assets.openfreemap.com/index.txt', timeout=30)
    r.raise_for_status()

    sprites_remote = [l for l in r.text.splitlines() if l.startswith('sprites/')]

    for sprite in sprites_remote:
        sprite_name = sprite.split('/')[1].replace('.tar.gz', '')

        if (sprites_dir / sprite_name).is_dir():
            continue

        url = f'https://assets.openfreemap.com/sprites/{sprite_name}.tar.gz'
        local_file = sprites_dir / 'temp.tar.gz'
        download_file_aria2(url, local_file)

        subprocess.run(
            ['tar', '-xzf', local_file, '-C', sprites_dir],
            check=True,
        )
        local_file.unlink()


def download_natural_earth(assets_dir: Path):
    ne_dir = assets_dir / 'natural_earth'

    if (ne_dir / 'tiles' / 'natural_earth_2_shaded_relief.raster' / '0' / '0' / '0.png').exists():
        return

    ne_dir.mkdir(exist_ok=True, parents=True)

    subprocess.run(
        [
            'git',
            'clone',
            '--depth=1',
            '-b',
            'gh-pages',
            'https://github.com/lukasmartinelli/naturalearthtiles.git',
            ne_dir,
        ]
    )

    shutil.rmtree(ne_dir / '.git')
