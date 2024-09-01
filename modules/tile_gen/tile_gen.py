#!/usr/bin/env python3

import click
from tile_gen_lib.btrfs import make_btrfs
from tile_gen_lib.planetiler import run_planetiler
from tile_gen_lib.rclone import make_indexes_for_bucket, upload_area
from tile_gen_lib.set_version import check_and_set_version


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

    upload_area(area)


@cli.command()
def make_indexes():
    """
    Make indexes for all buckets
    """

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

    check_and_set_version(area, version)


if __name__ == '__main__':
    cli()
