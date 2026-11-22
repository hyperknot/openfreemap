#!/usr/bin/env -S uv run python -P

import click

from tilegen.deploy_tilegen.install_planetiler import upload_planetiler_jar


@click.command()
def upload_planetiler() -> None:
    """
    Copy Planetiler's snapshot CI jar for the pinned commit to the assets bucket
    """
    upload_planetiler_jar()


if __name__ == '__main__':
    upload_planetiler()
