import json
from typing import Any

import click

from shared_lib.ssh_lib.utils import get_ip_from_ssh_alias
from shared_lib.utils.get_version import get_deployed_version
from shared_lib.utils.pycurl import pycurl_get


def check_server_health(config_data: dict[str, Any], hostname: str | None = None) -> dict[str, Any]:
    health_check_hosts = config_data.get('health_check', [])

    if hostname:
        health_check_hosts = [host for host in health_check_hosts if host == hostname]
        if not health_check_hosts:
            raise ValueError(f'Host {hostname} not found in health_check config')

    results: dict[str, Any] = {}
    if not health_check_hosts:
        return results

    area = 'monaco' if config_data.get('skip_planet') else 'planet'
    version = get_deployed_version(area)['version']
    domains = [d['domain'] for d in config_data['domains']]
    for health_check_host in health_check_hosts:
        server_hostname = health_check_host
        server_ip = get_ip_from_ssh_alias(health_check_host)
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


def print_server_health(results: dict[str, Any]) -> None:
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
