#!/usr/bin/env python3

import subprocess

import click
import questionary
from setversion_lib import RCLONE_BIN, RCLONE_CONF


@click.group()
def cli():
    """
    Sets deployed reference versions
    """


@cli.command()
@click.argument('area', required=True)
def interactive(area):
    versions = get_available_versions(area)[::-1]

    choices = [questionary.Choice(title=r, value=i) for i, r in enumerate(versions)]
    answer = questionary.select(f'Select version for: {area}', choices=choices).ask()

    selected = versions[answer]

    set_version(area, selected)


def get_available_versions(area):
    p = subprocess.run(
        [
            RCLONE_BIN,
            'cat',
            f'remote:ofm-{area}/dirs.txt',
        ],
        env=dict(RCLONE_CONFIG=RCLONE_CONF),
        check=True,
        capture_output=True,
        text=True,
    )
    versions = [l.strip() for l in p.stdout.strip().splitlines()]
    versions.sort()

    return versions


def set_version(area, version):
    subprocess.run(
        [
            RCLONE_BIN,
            'rcat',
            f'remote:ofm-assets/versions/deployed_{area}.txt',
        ],
        env=dict(RCLONE_CONFIG=RCLONE_CONF),
        check=True,
        input=version.encode(),
    )


if __name__ == '__main__':
    cli()
