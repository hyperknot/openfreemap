import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from tile_gen_lib.config import config


def run_planetiler(area: str) -> Path:
    assert area in config.areas

    date = datetime.now(tz=timezone.utc).strftime('%Y%m%d_%H%M%S')

    # delete all previous runs for the given area
    shutil.rmtree(config.runs_dir / area, ignore_errors=True)

    run_folder = config.runs_dir / area / f'{date}_pt'
    run_folder.mkdir(parents=True, exist_ok=True)

    os.chdir(run_folder)

    java_memory_gb = 30 if area == 'planet' else 1

    command = [
        'java',
        f'-Xmx{java_memory_gb}g',
        '-jar',
        config.planetiler_path,
        f'--area={area}',
        '--download',
        '--download-threads=10',
        '--download-chunk-size-mb=1000',
        '--fetch-wikidata',
        '--output=tiles.mbtiles',
        '--nodemap-type=array',
        '--storage=mmap',
        '--force',
    ]

    if area == 'planet':
        command += '--bounds=planet'

    out_path = run_folder / 'planetiler.out'
    err_path = run_folder / 'planetiler.err'

    with out_path.open('w') as out_file, err_path.open('w') as err_file:
        subprocess.run(command, stdout=out_file, stderr=err_file, check=True, cwd=run_folder)

    shutil.rmtree(run_folder / 'data', ignore_errors=True)
    print('planetiler.jar DONE')

    return run_folder
