#!/usr/bin/env -S uv run python -P

import os
import sys
from datetime import UTC, datetime

import click

from shared_lib.utils.telegram_v2_shared import send_telegram_message
from tilegen.tilegen_lib.btrfs import append_sha256sum, build_btrfs_image, gzip_btrfs, move_logs
from tilegen.tilegen_lib.lock import tile_build_lock
from tilegen.tilegen_lib.mbtiles import update_mbtiles_metadata
from tilegen.tilegen_lib.planetiler import fetch_wikidata_cache, run_planetiler
from tilegen.tilegen_lib.pmtiles import make_pmtiles
from tilegen.tilegen_lib.rclone import (
    finalize_run_upload,
    get_deployed_version_on_bucket,
    get_versions_on_bucket,
    make_indexes_for_bucket,
    set_version_on_bucket,
    upload_run_file,
)
from tilegen.tilegen_lib.tilegen_config import get_tilegen_config


now = datetime.now(UTC)


@click.group()
def cli():
    """
    Generates tiles and uploads to CloudFlare
    """


@cli.command()
@click.argument('area', required=True)
def fetch_wikidata(area: str):
    """Build or update the persistent Wikidata cache for an area."""
    print(f'---\n{now}\nStarting fetch-wikidata {area}')

    with tile_build_lock():
        fetch_wikidata_cache(area)


@cli.command()
@click.argument('area', required=True)
@click.option('--upload', is_flag=True, help='Upload after generation is complete')
def make_tiles(area: str, upload: bool):
    """
    Generate tiles for a given area, optionally upload it to the btrfs bucket
    """

    print(f'---\n{now}\nStarting make-tiles {area} upload: {upload}')

    if upload and not get_tilegen_config().rclone_config.exists():
        raise click.ClickException(f'rclone config not found: {get_tilegen_config().rclone_config}')

    with tile_build_lock():
        run_folder = run_planetiler(area)
        remote_dir = f'remote:ofm-btrfs/areas/{area}/{run_folder.name}'

        # mbtiles: update metadata, checksum and upload
        update_mbtiles_metadata(run_folder / 'tiles.mbtiles')
        append_sha256sum(run_folder / 'tiles.mbtiles', mode='w')
        if upload:
            upload_run_file(run_folder / 'tiles.mbtiles', remote_dir)

        # btrfs: create, checksum and upload
        build_btrfs_image(run_folder, area)
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
            minutes = int((datetime.now(UTC) - now).total_seconds() // 60)
            duration = f'{minutes // 60}h {minutes % 60}m' if minutes >= 60 else f'{minutes}m'
            _send_telegram(
                f'{area} {run_folder.name} uploaded (build {duration})', area, silent=True
            )
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

    # Reads go through the private R2 API (not the public URLs), so every error alerts.
    versions = get_versions_on_bucket(area)
    deployed = get_deployed_version_on_bucket(area)
    if not versions:
        raise click.ClickException(f'no versions on bucket: {area}')

    if version == 'latest':
        version = versions[-1]
        print(f'  Latest version on bucket: {area} {version}')
    elif version not in versions:
        raise click.ClickException(f'version is not complete: {area} {version}')

    if deployed == version:
        print(f'  Already deployed: {area} {version}')
        return

    set_version_on_bucket(area, version)
    _send_telegram(f'{area} deployed version set {deployed} → {version}', area, silent=True)


def _send_telegram(message: str, area: str | None, silent: bool = False):
    config = get_tilegen_config()
    send_telegram_message(
        message,
        token=config.telegram_token,
        chat_id=config.telegram_chat_id,
        topic_id=config.telegram_topic_id,
        header=f'Tilegen {area.title()}' if area else 'Tilegen',
        silent=silent,
    )


if __name__ == '__main__':
    if not os.environ.get('OFM_CRON'):
        cli()
    else:
        try:
            cli(standalone_mode=False)
        except Exception as e:
            area = next((arg for arg in sys.argv if arg in get_tilegen_config().areas), None)
            message = f'ERROR\n{type(e).__name__}: {e}'
            print(message)
            _send_telegram(message, area)
            raise
