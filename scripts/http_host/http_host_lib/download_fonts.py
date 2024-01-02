import shutil
import subprocess
from pathlib import Path

from http_host_lib.utils import download_if_size_differs


def download_fonts(assets_dir: Path):
    """
    Download and extract font assets if their file size differ.
    Making updates atomic, with extraction to a temp dest + rename
    """

    fonts_dir = assets_dir / 'fonts'
    fonts_dir.mkdir(exist_ok=True, parents=True)

    fonts_temp = assets_dir / 'fonts_temp'

    for font in ['ml', 'omt', 'pm']:
        url = f'https://assets.openfreemap.com/fonts/{font}.tgz'
        local_file = fonts_dir / f'{font}.tgz'
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
