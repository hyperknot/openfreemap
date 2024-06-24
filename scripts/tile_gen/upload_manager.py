#!/usr/bin/env python3
import json
import pathlib
import shutil
import subprocess

import click


AREAS = ['planet', 'monaco']

RUNS_DIR = pathlib.Path('/data/ofm/tile_gen/runs')


def upload_rclone(area, run):
    subprocess.run(
        [
            'rclone',
            'sync',
            '--transfers=8',
            '--multi-thread-streams=8',
            '--fast-list',
            '-v',
            '--stats-file-name-length',
            '0',
            '--stats-one-line',
            '--log-file',
            RUNS_DIR / area / run / 'logs' / 'rclone.log',
            '--exclude',
            'logs/**',
            RUNS_DIR / area / run,
            f'remote:ofm-{area}/{run}',
        ],
        env=dict(RCLONE_CONFIG='/data/ofm/config/rclone.conf'),
        check=True,
    )


def make_indexes():
    for area in AREAS:
        print(f'creating index {area}')

        # files
        p = subprocess.run(
            [
                'rclone',
                'lsf',
                '-R',
                '--files-only',
                '--fast-list',
                '--exclude',
                'dirs.txt',
                '--exclude',
                'index.txt',
                f'remote:ofm-{area}',
            ],
            env=dict(RCLONE_CONFIG='/data/ofm/config/rclone.conf'),
            check=True,
            capture_output=True,
            text=True,
        )
        index_str = p.stdout

        subprocess.run(
            [
                'rclone',
                'rcat',
                f'remote:ofm-{area}/index.txt',
            ],
            env=dict(RCLONE_CONFIG='/data/ofm/config/rclone.conf'),
            check=True,
            input=index_str.encode(),
        )

        # directories
        p = subprocess.run(
            [
                'rclone',
                'lsf',
                '-R',
                '--dirs-only',
                '--dir-slash=false',
                '--fast-list',
                f'remote:ofm-{area}',
            ],
            env=dict(RCLONE_CONFIG='/data/ofm/config/rclone.conf'),
            check=True,
            capture_output=True,
            text=True,
        )
        index_str = p.stdout

        subprocess.run(
            [
                'rclone',
                'rcat',
                f'remote:ofm-{area}/dirs.txt',
            ],
            env=dict(RCLONE_CONFIG='/data/ofm/config/rclone.conf'),
            check=True,
            input=index_str.encode(),
        )


@click.group()
def cli():
    """
    Uploads runs to Cloudflare
    """


@cli.command()
def upload_runs():
    """
    Upload all runs present in system
    """

    print('running upload_runs')

    for area in AREAS:
        if not (RUNS_DIR / area).exists():
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
        runs_local = {p.name for p in (RUNS_DIR / area).iterdir()}

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
