#!/usr/bin/env python3
from datetime import datetime, timezone

import click
from tile_gen_lib.btrfs import append_sha256sum, gzip_btrfs, make_btrfs, move_logs
from tile_gen_lib.get_version_shared import (
    get_deployed_version,
    get_versions_for_area,
)
from tile_gen_lib.planetiler import run_planetiler
from tile_gen_lib.rclone import (
    finish_run_upload,
    make_indexes_for_bucket,
    set_version_on_bucket,
    upload_area,
    upload_run_file,
)


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
    remote_dir = f'remote:ofm-btrfs/areas/{area}/{run_folder.name}'

    # mbtiles: checksum and upload
    append_sha256sum(run_folder / 'tiles.mbtiles', mode='w')
    if upload:
        upload_run_file(run_folder / 'tiles.mbtiles', remote_dir)

    # btrfs: create, checksum, upload
    make_btrfs(run_folder)
    append_sha256sum(run_folder / 'tiles.btrfs')
    if upload:
        upload_run_file(run_folder / 'tiles.btrfs', remote_dir)

    # gzip btrfs (pigz removes original), checksum, upload
    gzip_btrfs(run_folder)
    append_sha256sum(run_folder / 'tiles.btrfs.gz')
    if upload:
        upload_run_file(run_folder / 'tiles.btrfs.gz', remote_dir)

    # finalize
    move_logs(run_folder)
    if upload:
        finish_run_upload(run_folder, remote_dir)
        make_indexes_for_bucket('ofm-btrfs')


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
