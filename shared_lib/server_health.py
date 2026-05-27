import json

import click

from shared_lib.get_version_shared import get_deployed_version
from shared_lib.pycurl import pycurl_get
from shared_lib.ssh_lib.utils import get_ip_from_ssh_alias


def check_server_health(config_data: dict, hostname: str | None = None) -> dict:
    area = 'monaco' if config_data.get('skip_planet') else 'planet'
    version = get_deployed_version(area)['version']
    domains = [d['domain'] for d in config_data['domains']]
    servers = [
        {'hostname': s['hostname'], 'ip': get_ip_from_ssh_alias(s['hostname'])}
        for s in config_data['servers']
    ]

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
