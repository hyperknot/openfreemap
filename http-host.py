#!/usr/bin/env python3
import json
from pprint import pprint

import click

from modules.http_host.http_host_lib.get_version_shared import get_deployed_version
from ssh_lib.cli_helpers import common_options, get_connection
from ssh_lib.config import config
from ssh_lib.pycurl import pycurl_get
from ssh_lib.tasks_http_host import prepare_http_host, read_jsonc, run_http_host_sync
from ssh_lib.tasks_shared import prepare_shared
from ssh_lib.utils import (
    get_ip_from_ssh_alias,
    put,
)


@click.group()
def cli():
    pass


@cli.command()
@common_options
def init_static(hostname, user, port, noninteractive):
    if not noninteractive and not click.confirm(f'Run script on {hostname}?'):
        return

    c = get_connection(hostname, user, port)

    prepare_shared(c)
    prepare_http_host(c)

    run_http_host_sync(c)


@cli.command()
@common_options
@click.option('--sync', is_flag=True, help='Run manual sync after init')
def init_autoupdate(hostname, user, port, noninteractive, sync):
    if not noninteractive and not click.confirm(f'Run script on {hostname}?'):
        return

    c = get_connection(hostname, user, port)

    c.sudo('rm -f /etc/cron.d/ofm_http_host')

    prepare_shared(c)
    prepare_http_host(c)

    # if --sync, run manual sync
    if sync:
        run_http_host_sync(c)

    put(c, config.local_modules_dir / 'http_host' / 'cron.d' / 'ofm_http_host', '/etc/cron.d/')


@cli.command()
@common_options
def sync(hostname, user, port, noninteractive):
    if not noninteractive and not click.confirm(f'Run script on {hostname}?'):
        return

    c = get_connection(hostname, user, port)
    run_http_host_sync(c)


@cli.command()
def debug():
    config_data = read_jsonc()
    area = 'monaco' if config_data.get('skip_planet') else 'planet'
    version = get_deployed_version(area)['version']
    domains = [d['domain'] for d in config_data['domains']]
    servers = [
        {'hostname': s['hostname'], 'ip': get_ip_from_ssh_alias(s['hostname'])}
        for s in config_data['servers']
    ]

    for server in servers:
        print(f'SERVER {server["hostname"]} ({server["ip"]})')
        server_ok = True

        for domain in domains:
            try:
                check_host_using_tilejson(
                    url=f'https://{domain}/{area}/{version}',
                    ip=server['ip'],
                    version=version,
                )
                print(f'  {domain}     OK')
            except AssertionError:
                print(f'  {domain}     FAILED - Version mismatch (expected {version})')
                server_ok = False
            except Exception as e:
                print(f'  {domain}     FAILED - {e}')
                server_ok = False

        status = 'OK' if server_ok else 'FAILED'
        print(f'  {status}\n')


def check_host_using_tilejson(*, url: str, ip: str, version: str) -> None:
    tilejson_str = pycurl_get(url, ip)
    tilejson = json.loads(tilejson_str)
    tiles_url = tilejson['tiles'][0]
    version_in_tilejson = tiles_url.split('/')[4]
    assert version_in_tilejson == version


if __name__ == '__main__':
    cli()
