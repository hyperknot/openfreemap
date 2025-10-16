#!/usr/bin/env python3
import json

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

    # Check server health after deployment
    results = check_server_health(hostname)
    print_server_health(results)


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

    # Check server health after deployment
    results = check_server_health(hostname)
    print_server_health(results)


@cli.command()
@common_options
def sync(hostname, user, port, noninteractive):
    if not noninteractive and not click.confirm(f'Run script on {hostname}?'):
        return

    c = get_connection(hostname, user, port)
    run_http_host_sync(c)

    # Check server health after sync
    results = check_server_health(hostname)
    print_server_health(results)


@cli.command()
@click.option('--hostname', help='Check only a specific server')
def debug(hostname):
    results = check_server_health(hostname)
    print_server_health(results)


def check_server_health(hostname: str = None) -> dict:
    """
    Check health of servers by verifying deployed version matches expected version.

    Args:
        hostname: Optional hostname to check. If None, checks all servers in config.

    Returns:
        dict: Results for each server with structure:
            {
                'server_hostname': {
                    'ip': '1.2.3.4',
                    'all_ok': True/False,
                    'domains': {
                        'domain.com': {'status': 'ok'/'failed', 'error': None/'error message'}
                    }
                }
            }
    """
    config_data = read_jsonc()
    area = 'monaco' if config_data.get('skip_planet') else 'planet'
    version = get_deployed_version(area)['version']
    domains = [d['domain'] for d in config_data['domains']]

    servers = [
        {'hostname': s['hostname'], 'ip': get_ip_from_ssh_alias(s['hostname'])}
        for s in config_data['servers']
    ]

    # Filter to specific server if requested
    if hostname:
        servers = [s for s in servers if s['hostname'] == hostname]
        if not servers:
            raise ValueError(f'Server {hostname} not found in config')

    results = {}

    for server in servers:
        server_hostname = server['hostname']
        server_ip = server['ip']
        results[server_hostname] = {'ip': server_ip, 'domains': {}, 'all_ok': True}

        for domain in domains:
            try:
                check_host_using_tilejson(
                    url=f'https://{domain}/{area}/{version}',
                    ip=server_ip,
                    version=version,
                )
                results[server_hostname]['domains'][domain] = {'status': 'ok', 'error': None}
            except AssertionError:
                results[server_hostname]['domains'][domain] = {
                    'status': 'failed',
                    'error': f'Version mismatch (expected {version})',
                }
                results[server_hostname]['all_ok'] = False
            except Exception as e:
                results[server_hostname]['domains'][domain] = {'status': 'failed', 'error': str(e)}
                results[server_hostname]['all_ok'] = False

    return results


def print_server_health(results: dict) -> None:
    """Print server health results in a human-readable format."""
    for server_hostname, server_data in results.items():
        status = (
            click.style('OK', fg='green')
            if server_data['all_ok']
            else click.style('FAILED', fg='red')
        )
        server_line = f'SERVER {server_hostname} ({server_data["ip"]})'
        print(f'{server_line:<50} {status}')

        for domain, domain_data in server_data['domains'].items():
            domain_line = f'  {domain}'
            if domain_data['status'] == 'ok':
                print(f'{domain_line:<50} {click.style("OK", fg="green")}')
            else:
                print(
                    f'{domain_line:<50} {click.style("FAILED", fg="red")}\n  {domain_data["error"]}'
                )

        print()


def check_host_using_tilejson(*, url: str, ip: str, version: str) -> None:
    tilejson_str = pycurl_get(url, ip)
    tilejson = json.loads(tilejson_str)
    tiles_url = tilejson['tiles'][0]
    version_in_tilejson = tiles_url.split('/')[4]
    assert version_in_tilejson == version


if __name__ == '__main__':
    cli()
