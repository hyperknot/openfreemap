import os
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from tilegen.tilegen_lib.tilegen_config import get_tilegen_config

from .btrfs import cleanup_folder


def fetch_wikidata_cache(area: str) -> None:
    assert area in get_tilegen_config().areas

    wikidata_dir = get_tilegen_config().tilegen_dir / 'wikidata' / area
    wikidata_dir.mkdir(parents=True, exist_ok=True)
    command = _planetiler_command(area, wikidata_dir / 'geotools')
    command.extend(['--only-fetch-wikidata', f'--wikidata-cache={_wikidata_cache_path(area)}'])
    print(command)

    with (
        (wikidata_dir / 'planetiler_out.log').open('w') as out_file,
        (wikidata_dir / 'planetiler_err.log').open('w') as err_file,
    ):
        subprocess.run(command, stdout=out_file, stderr=err_file, check=True, cwd=wikidata_dir)


def run_planetiler(area: str) -> Path:
    assert area in get_tilegen_config().areas

    wikidata_cache_path = _wikidata_cache_path(area)
    wikidata_cache_path.parent.mkdir(parents=True, exist_ok=True)
    date = datetime.now(UTC).strftime('%Y%m%d_%H%M%S')

    area_dir = get_tilegen_config().runs_dir / area

    # delete all previous runs for the given area
    if area_dir.is_dir():
        for subdir in area_dir.iterdir():
            cleanup_folder(subdir)

        print('running rmtree')
        shutil.rmtree(area_dir, ignore_errors=True)
        print('rmtree done')

    run_folder = area_dir / f'{date}_pt'
    run_folder.mkdir(parents=True, exist_ok=True)

    os.chdir(run_folder)

    command = _planetiler_command(area, run_folder / 'geotools')
    command.extend(
        [
            '--fetch-wikidata',
            f'--wikidata-cache={wikidata_cache_path}',
            '--output=tiles.mbtiles',
            '--storage=mmap',
            '--languages=default,tok',
            '--transliterate=false',
        ]
    )

    if area == 'planet':
        command.extend(['--nodemap-type=array', '--bounds=planet'])
    elif area == 'monaco':
        command.append('--nodemap-type=sortedtable')

    print(command)

    out_path = run_folder / 'planetiler_out.log'
    err_path = run_folder / 'planetiler_err.log'

    try:
        with out_path.open('w') as out_file, err_path.open('w') as err_file:
            subprocess.run(command, stdout=out_file, stderr=err_file, check=True, cwd=run_folder)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f'Planetiler failed with exit code {e.returncode}; see {err_path}'
        ) from e

    shutil.rmtree(run_folder / 'data', ignore_errors=True)
    print('planetiler.jar DONE')

    return run_folder


def _wikidata_cache_path(area: str) -> Path:
    # Outside /data/ofm, so --reinstall keeps it.
    return Path('/data/ofm_keep/wikidata') / f'{area}.json'


def _planetiler_command(area: str, geotools_dir: Path) -> list[str | Path]:
    # https://github.com/onthegomap/planetiler/discussions/690#discussioncomment-7756397
    java_memory_gb = 30 if area == 'planet' else 1
    tilegen_config = get_tilegen_config()

    return [
        'java',
        f'-Xmx{java_memory_gb}g',
        f'-DEPSG-HSQL.directory={geotools_dir}',
        '-cp',
        tilegen_config.planetiler_path,
        tilegen_config.planetiler_profile,
        f'--area={area}',
        '--download',
        '--download-threads=10',
        '--download-chunk-size-mb=1000',
        '--http-timeout=60s',
        '--http-retries=10',
        '--http-retry-wait=30s',
        '--force',
    ]
