#!/usr/bin/env python3

import json
import subprocess
from pathlib import Path

import click
from tile_gen_lib.config import config
from tile_gen_lib.extract import make_btrfs
from tile_gen_lib.planetiler import run_planetiler
from tile_gen_lib.upload import make_indexes, upload_rclone


@click.group()
def cli():
    """
    Generates tiles and uploads to CloudFlare
    """


@cli.command()
@click.argument('area', required=True)
def make_tiles(area):
    """
    Generate tiles for a given area
    """

    # run_planetiler(area)
    make_btrfs(Path('/data/ofm/tile_gen/runs/monaco/20240826_230406_pt'))


@cli.command()
def upload_runs():
    """
    Upload all runs present in system
    """

    print('running upload_runs')

    for area in config.areas:
        if not (config.runs_dir / area).exists():
            continue

        p = subprocess.run(
            [
                'rclone',
                'lsjson',
                '--dirs-only',
                '--fast-list',
                f'remote:ofm-{area}',
            ],
            text=True,
            capture_output=True,
            check=True,
            env=dict(RCLONE_CONFIG='/data/ofm/config/rclone.conf'),
        )
        rclone_json = json.loads(p.stdout)
        runs_remote = {p['Path'] for p in rclone_json}
        runs_local = {p.name for p in (config.runs_dir / area).iterdir()}

        runs_to_upload = runs_local - runs_remote
        for run in runs_to_upload:
            print(f'uploading {area} {run}')
            upload_rclone(area, run)

    make_indexes()


@cli.command()
def index():
    """
    Run index on Cloudflare buckets
    """

    make_indexes()


if __name__ == '__main__':
    cli()
