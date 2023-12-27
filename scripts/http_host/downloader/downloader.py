#!/usr/bin/env python3

import click


@click.command()
@click.option('--area', default='planet', help='The area to process')
@click.option('--version', default='latest', help='Version string, like "20231227_043106_pt"')
def cli(area, version):
    click.echo(f'Area: {area}, version: {version}')


if __name__ == '__main__':
    cli()
