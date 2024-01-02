#!/usr/bin/env python3
import datetime
import shutil
import subprocess
import sys
from pathlib import Path

import click
import requests


DEFAULT_RUNS_DIR = Path('/data/ofm/http_host/runs')


@click.command()
@click.argument('area', required=False)
@click.option('--version', default='latest', help='Version string, like "20231227_043106_pt"')
@click.option(
    '--runs-dir',
    help='Specify /runs directory',
    type=click.Path(dir_okay=True, file_okay=False, path_type=Path),
)
@click.option('--list-versions', is_flag=True, help='List all versions in an area and terminate')
@click.option('--run-mounter', is_flag=True, help='Run mounter.py after download is complete')
def cli(area: str, version: str, list_versions: bool, runs_dir: Path, run_mounter: bool):
    """
    Downloads and extracts the latest tiles.btrfs file from the public bucket.
    Specific version can also be specified.
    """

    print(datetime.datetime.now(tz=datetime.timezone.utc))

    if area not in {'planet', 'monaco'}:
        sys.exit('Please specify are: "planet" or "monaco"')

    r = requests.get(f'https://{area}.openfreemap.com/dirs.txt')
    r.raise_for_status()

    versions = sorted(r.text.splitlines())

    all_versions_str = '\n'.join(versions)
    if list_versions:
        print(all_versions_str)
        return

    if version == 'latest':
        selected_version = versions[-1]
    else:
        if version not in versions:
            sys.exit(f'Requested version is not available. Available versions:\n{all_versions_str}')
        selected_version = version

    if not runs_dir and not Path('/data/ofm').exists():
        sys.exit('Please specify a runs dir with --runs-dir')

    changed = download(area, selected_version, runs_dir or DEFAULT_RUNS_DIR)

    if changed and run_mounter:
        print('running mounter.py')

        subprocess.run(
            [sys.executable, Path(__file__).parent / 'mounter.py'],
            check=True,
        )

    print('\n\n\n')


def download(area: str, version: str, runs_dir: Path) -> bool:
    click.echo(f'Downloading: area: {area}, version: {version}')

    version_dir = runs_dir / area / version
    btrfs_file = version_dir / 'tiles.btrfs'
    if btrfs_file.exists():
        print('File exists, skipping download')
        return False

    temp_dir = runs_dir / '_tmp'
    if temp_dir.exists():
        sys.exit(f'{temp_dir} dir exists, please delete it first')

    temp_dir.mkdir(parents=True)

    url = f'https://{area}.openfreemap.com/{version}/tiles.btrfs.gz'
    print(url)

    subprocess.run(
        [
            'aria2c',
            '--split=8',
            '--max-connection-per-server=8',
            '--file-allocation=none',
            '--dir',
            temp_dir,
            url,
        ],
        check=True,
    )

    subprocess.run(['unpigz', temp_dir / 'tiles.btrfs.gz'], check=True)
    btrfs_src = temp_dir / 'tiles.btrfs'

    shutil.rmtree(version_dir, ignore_errors=True)
    version_dir.mkdir(parents=True)

    btrfs_src.rename(btrfs_file)

    shutil.rmtree(temp_dir)

    return True


if __name__ == '__main__':
    cli()
