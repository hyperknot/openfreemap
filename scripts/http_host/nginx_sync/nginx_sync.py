#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

import click


@click.command()
def cli():
    if not Path('/etc/fstab').exists():
        sys.exit('Needs to be run on Linux')

    if os.geteuid() != 0:
        sys.exit('Needs sudo')

    if not Path('/mnt/ofm').exists():
        sys.exit('mounter.py needs to be run first')

    with open(Path(__file__).parent / 'nginx_site.conf') as fp:
        nginx_template = fp.read()

    location_block_str = ''
    help_text = ''

    for subdir in Path('/mnt/ofm').iterdir():
        if not subdir.is_dir():
            continue

        area, version = subdir.name.split('-')

        version_str = rf"""
            location /{area}/{version}/ {{
                alias {subdir};
                try_files $uri @empty;
            }}
            """

        location_block_str += version_str

        if not help_text:
            help_text = (
                '\ntest with:\n'
                f'curl -H "Host: ofm" -I http://localhost/{area}/{version}/tiles/14/8529/5975.pbf'
            )

    nginx_template = nginx_template.replace('___LOCATION_BLOCKS___', location_block_str)

    with open('/data/nginx/sites/ofm.conf', 'w') as fp:
        fp.write(nginx_template)
        print('nginx config written')

    subprocess.run(['nginx', '-t'], check=True)
    subprocess.run(['service', 'nginx', 'reload'], check=True)

    print(help_text)


if __name__ == '__main__':
    cli()
