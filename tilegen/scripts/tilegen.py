#!/usr/bin/env -S uv run python -P

import os
import sys
from datetime import UTC, datetime, timedelta

import click

from shared_lib.utils.telegram_v2_shared import send_telegram_message
from tilegen.tilegen_lib.btrfs import append_sha256sum, build_btrfs_image, move_logs
from tilegen.tilegen_lib.lock import tile_build_lock
from tilegen.tilegen_lib.mbtiles import update_mbtiles_metadata
from tilegen.tilegen_lib.planetiler import fetch_wikidata_cache, run_planetiler
from tilegen.tilegen_lib.pmtiles import make_pmtiles
from tilegen.tilegen_lib.rclone import (
    delete_run_on_bucket,
    finalize_run_upload,
    get_deployed_version_on_bucket,
    get_runs_on_bucket,
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

        # delete btrfs file to save space
        (run_folder / 'tiles.btrfs').unlink()

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
    print(f'  Deployed version set: {area} {deployed} → {version}')


@cli.command()
@click.option('--dry-run', is_flag=True, help='Only print the runs that would be deleted')
def purge_versions(dry_run: bool):
    """
    Delete old runs from the btrfs bucket

    Keeps the deployed version, the last 4 complete runs and the first complete run
    of each of the last 6 months with runs. Incomplete runs are deleted after 7 days.
    """

    print(f'---\n{now}\nStarting purge-versions dry-run: {dry_run}')

    incomplete_cutoff = (now - timedelta(days=7)).strftime('%Y%m%d_%H%M%S')
    deleted_any = False

    for area in get_tilegen_config().areas:
        versions = get_versions_on_bucket(area)
        deployed = get_deployed_version_on_bucket(area)
        if not deployed:
            raise click.ClickException(f'no deployed version: {area}')

        first_of_month: dict[str, str] = {}
        for version in versions:
            first_of_month.setdefault(version[:6], version)
        monthly = [first_of_month[month] for month in sorted(first_of_month)[-6:]]
        keep = {deployed, *versions[-4:], *monthly}

        to_delete = [
            run
            for run in get_runs_on_bucket(area)
            if run not in keep and (run in versions or run < incomplete_cutoff)
        ]
        print(f'  {area}: keeping {sorted(keep)}')
        print(f'  {area}: deleting {to_delete}')
        if dry_run or not to_delete:
            continue

        for run in to_delete:
            delete_run_on_bucket(area, run)
        deleted_any = True

    if deleted_any:
        make_indexes_for_bucket('ofm-btrfs')


def _send_telegram(message: str, area: str | None):
    config = get_tilegen_config()
    send_telegram_message(
        message,
        token=config.telegram_token,
        chat_id=config.telegram_chat_id,
        topic_id=config.telegram_topic_id,
        header=f'Tilegen {area.title()}' if area else 'Tilegen',
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
