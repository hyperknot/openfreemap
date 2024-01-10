import shutil
import subprocess
from pathlib import Path

import requests

from http_host_lib.utils import download_file_aria2, download_if_size_differs


def download_fonts(assets_dir: Path):
    """
    Download and extract font assets if their file size differ.
    Making updates atomic, with extraction to a temp dest + rename
    """

    fonts_dir = assets_dir / 'fonts'
    fonts_dir.mkdir(exist_ok=True, parents=True)

    fonts_temp = assets_dir / 'fonts_temp'

    for font in ['ofm']:
        url = f'https://assets.openfreemap.com/fonts/{font}.tar.gz'
        local_file = fonts_dir / f'{font}.tar.gz'
        if not download_if_size_differs(url, local_file):
            continue

        shutil.rmtree(fonts_temp, ignore_errors=True)
        fonts_temp.mkdir()

        subprocess.run(
            ['tar', '-xzf', local_file, '-C', fonts_temp],
            check=True,
        )

        target_dir = fonts_dir / font
        target_dir_renamed = fonts_dir / f'{font}.bak'
        temp_dir = fonts_temp / font

        if target_dir.exists():
            target_dir.rename(target_dir_renamed)
        temp_dir.rename(target_dir)

        shutil.rmtree(target_dir_renamed, ignore_errors=True)

    shutil.rmtree(fonts_temp, ignore_errors=True)


def download_sprites(assets_dir: Path):
    """
    Download and extract sprites if their file size differ.
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
