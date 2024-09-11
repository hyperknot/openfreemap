import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from tile_gen_lib.btrfs import cleanup_folder
from tile_gen_lib.config import config


def run_planetiler(area: str) -> Path:
    assert area in config.areas

    date = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')

    area_dir = config.runs_dir / area

    # delete all previous runs for the given area
    for subdir in area_dir.iterdir():
        cleanup_folder(subdir)

    print('running rmtree')
    shutil.rmtree(area_dir, ignore_errors=True)
    print('rmtree done')

    run_folder = area_dir / f'{date}_pt'
    run_folder.mkdir(parents=True, exist_ok=True)

    os.chdir(run_folder)

    # link to discussion about why exactly 30 GB
    # https://github.com/onthegomap/planetiler/discussions/690#discussioncomment-7756397
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
        command.append('--bounds=planet')

    print(command)

    out_path = run_folder / 'planetiler.out'
    err_path = run_folder / 'planetiler.err'

    with out_path.open('w') as out_file, err_path.open('w') as err_file:
        subprocess.run(command, stdout=out_file, stderr=err_file, check=True, cwd=run_folder)

    shutil.rmtree(run_folder / 'data', ignore_errors=True)
    print('planetiler.jar DONE')

    return run_folder
