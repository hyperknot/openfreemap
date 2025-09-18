#!/usr/bin/env python3
from datetime import datetime, timezone

import click
from tile_gen_lib.btrfs import make_btrfs
from tile_gen_lib.get_version_shared import (
    get_deployed_version,
    get_versions_for_area,
)
from tile_gen_lib.planetiler import run_planetiler
from tile_gen_lib.rclone import make_indexes_for_bucket, set_version_on_bucket, upload_area


now = datetime.now(timezone.utc)


@click.group()
def cli():
    """
    Generates tiles and uploads to CloudFlare
    """


@cli.command()
@click.argument('area', required=True)
@click.option('--upload', is_flag=True, help='Upload after generation is complete')
def make_tiles(area, upload):
    """
    Generate tiles for a given area, optionally upload it to the btrfs bucket
    """

    print(f'---\n{now}\nStarting make-tiles {area} upload: {upload}')

    run_folder = run_planetiler(area)
    make_btrfs(run_folder)

    if upload:
        upload_area(area)


@cli.command(name='upload-area')
@click.argument('area', required=True)
def upload_area_(area):
    """
    Upload all runs from a given area to the btrfs bucket
    """

    print(f'---\n{now}\nStarting upload-area {area}')

    upload_area(area)


@cli.command()
def make_indexes():
    """
    Make indexes for all buckets
    """

    print(f'---\n{now}\nStarting make-indexes')

    for bucket in ['ofm-btrfs', 'ofm-assets']:
        make_indexes_for_bucket(bucket)


@cli.command()
@click.argument('area', required=True)
@click.option(
    '--version', default='latest', help='Optional version string, like "20231227_043106_pt"'
)
def set_version(area, version):
    """
    Set versions for a given area
    """

    print(f'---\n{now}\nStarting set-version {area}')

    if version == 'latest':
        versions = get_versions_for_area(area)
        if not versions:
            print(f'  No versions found for {area}')
            return

        version = versions[-1]
        print(f'  Latest version on bucket: {area} {version}')

    try:
        if get_deployed_version(area)['version'] == version:
            return
    except Exception:
        pass

    set_version_on_bucket(area, version)


if __name__ == '__main__':
    cli()
