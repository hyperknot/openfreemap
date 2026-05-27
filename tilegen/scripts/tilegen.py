#!/usr/bin/env -S uv run python -P

from datetime import UTC, datetime

import click

from shared_lib.get_version_shared import get_deployed_version, get_versions_for_area
from tilegen.tilegen_lib.btrfs import append_sha256sum, gzip_btrfs, make_btrfs, move_logs
from tilegen.tilegen_lib.mbtiles import update_mbtiles_metadata
from tilegen.tilegen_lib.planetiler import run_planetiler
from tilegen.tilegen_lib.pmtiles import make_pmtiles
from tilegen.tilegen_lib.rclone import (
    finalize_run_upload,
    make_indexes_for_bucket,
    set_version_on_bucket,
    upload_run_file,
)
from tilegen.tilegen_lib.tilegen_config import tilegen_config


now = datetime.now(UTC)


@click.group()
def cli():
    """
    Generates tiles and uploads to CloudFlare
    """


@cli.command()
@click.argument('area', required=True)
@click.option('--upload', is_flag=True, help='Upload after generation is complete')
def make_tiles(area: str, upload: bool):
    """
    Generate tiles for a given area, optionally upload it to the btrfs bucket
    """

    print(f'---\n{now}\nStarting make-tiles {area} upload: {upload}')

    if upload and not tilegen_config.rclone_config.exists():
        raise click.ClickException(f'rclone config not found: {tilegen_config.rclone_config}')

    run_folder = run_planetiler(area)
    remote_dir = f'remote:ofm-btrfs/areas/{area}/{run_folder.name}'

    # mbtiles: update metadata, checksum and upload
    update_mbtiles_metadata(run_folder / 'tiles.mbtiles')
    append_sha256sum(run_folder / 'tiles.mbtiles', mode='w')
    if upload:
        upload_run_file(run_folder / 'tiles.mbtiles', remote_dir)

    # btrfs: create, checksum and upload
    make_btrfs(run_folder, area)
    append_sha256sum(run_folder / 'tiles.btrfs')
    if upload:
        upload_run_file(run_folder / 'tiles.btrfs', remote_dir)

    # gzip btrfs (pigz removes original), checksum, upload
    gzip_btrfs(run_folder)
    append_sha256sum(run_folder / 'tiles.btrfs.gz')
    if upload:
        upload_run_file(run_folder / 'tiles.btrfs.gz', remote_dir)

    # delete btrfs files to save space
    for btrfs_file in [run_folder / 'tiles.btrfs', run_folder / 'tiles.btrfs.gz']:
        btrfs_file.unlink(missing_ok=True)

    # pmtiles: create from mbtiles, checksum and upload
    make_pmtiles(run_folder)
    append_sha256sum(run_folder / 'tiles.pmtiles')
    if upload:
        upload_run_file(run_folder / 'tiles.pmtiles', remote_dir)

    # finalize
    move_logs(run_folder)
    if upload:
        finalize_run_upload(run_folder, remote_dir)
        make_indexes_for_bucket('ofm-btrfs')


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
def set_version(area: str, version: str):
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
