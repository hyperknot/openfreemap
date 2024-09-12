#!/usr/bin/env python3

from datetime import datetime, timezone

import click
from loadbalancer_lib.loadbalance import check_or_fix


now = datetime.now(timezone.utc)


@click.group()
def cli():
    """
    Manages load-balancing of Round-Robin DNS records
    """


@cli.command()
def check():
    """
    Runs load-balancing check
    """

    print(f'---\n{now}\nStarting check')
    check_or_fix(fix=False)


@cli.command()
def fix():
    """
    Runs check and fixes records based on check results
    """

    print(f'---\n{now}\nStarting fix')
    check_or_fix(fix=True)


if __name__ == '__main__':
    cli()
