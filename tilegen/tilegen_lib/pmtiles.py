import subprocess
from pathlib import Path

from tilegen.tilegen_lib.tilegen_config import tilegen_config


def make_pmtiles(run_folder: Path):
    subprocess.run(
        [tilegen_config.pmtiles_path, 'convert', 'tiles.mbtiles', 'tiles.pmtiles'],
        cwd=run_folder,
        check=True,
    )
    subprocess.run(
        [tilegen_config.pmtiles_path, 'verify', 'tiles.pmtiles'], cwd=run_folder, check=True
    )
    print('make_pmtiles DONE')
