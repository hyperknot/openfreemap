import json
import time
from pathlib import Path
from typing import Any

import click

from shared_lib.ssh_lib.utils import get_ip_from_ssh_alias
from shared_lib.utils.get_version import get_deployed_version
from shared_lib.utils.pycurl import pycurl_get


def check_server_health(
    jsonc_data: dict[str, Any], hostname: str | None = None, *, print_results: bool = False
) -> dict[str, Any]:
    health_check_hosts = jsonc_data.get('health_check', [])

    if hostname:
        health_check_hosts = [host for host in health_check_hosts if host == hostname]
        if not health_check_hosts:
            raise ValueError(f'Host {hostname} not found in health_check config')

    results: dict[str, Any] = {}
    if not health_check_hosts:
        return results

    area = 'monaco' if jsonc_data.get('skip_planet') else 'planet'
    version = get_deployed_version(area)['version']
    for health_check_host in health_check_hosts:
        server_hostname = health_check_host
        server_ip = get_ip_from_ssh_alias(server_hostname)
        results[server_hostname] = {'ip': server_ip, 'domains': {}, 'all_ok': True}

        for domain_data in jsonc_data['domains']:
            domain = domain_data['domain']
            checks = _domain_health_checks(domain_data)
            results[server_hostname]['domains'][domain] = {}

            for check in checks:
                check_name = check['name']
                try:
                    check_host_using_tilejson(
                        url=f'https://{domain}/{area}/{version}',
                        version=version,
                        ip=server_ip if check['use_origin_ip'] else None,
                        validate_certs=check['validate_certs'],
                        ca_cert_path=check['ca_cert_path'],
                    )
                    results[server_hostname]['domains'][domain][check_name] = {
                        'status': 'ok',
                        'error': None,
                    }
                except AssertionError:
                    results[server_hostname]['domains'][domain][check_name] = {
                        'status': 'failed',
                        'error': f'Version mismatch (expected {version})',
                    }
                    results[server_hostname]['all_ok'] = False
                except Exception as e:
                    results[server_hostname]['domains'][domain][check_name] = {
                        'status': 'failed',
                        'error': str(e),
                    }
                    results[server_hostname]['all_ok'] = False

    if print_results:
        _print_server_health(results)

    return results


def check_host_using_tilejson(
    *,
    url: str,
    version: str,
    ip: str | None = None,
    validate_certs: bool = True,
    ca_cert_path: str | None = None,
) -> None:
    last_error: Exception | None = None

    for _ in range(30):
        try:
            tilejson_str = pycurl_get(
                url, ip, validate_certs=validate_certs, ca_cert_path=ca_cert_path
            )
            tilejson = json.loads(tilejson_str)
            tiles_url = tilejson['tiles'][0]
            version_in_tilejson = tiles_url.split('/')[4]
            assert version_in_tilejson == version
            return
        except AssertionError:
            raise
        except Exception as e:
            last_error = e
            time.sleep(1)

    if last_error:
        raise last_error


def _domain_health_checks(domain_data: dict[str, Any]) -> list[dict[str, Any]]:
    cert = domain_data['cert']
    cert_type = cert['type']

    if cert_type == 'upload':
        return [
            {
                'name': 'origin',
                'use_origin_ip': True,
                'validate_certs': True,
                'ca_cert_path': _uploaded_cert_path(cert),
            },
            {
                'name': 'edge',
                'use_origin_ip': False,
                'validate_certs': True,
                'ca_cert_path': None,
            },
        ]

    if cert_type == 'dummy':
        return [
            {
                'name': 'origin',
                'use_origin_ip': True,
                'validate_certs': False,
                'ca_cert_path': None,
            }
        ]

    if cert_type == 'letsencrypt':
        return [
            {
                'name': 'origin',
                'use_origin_ip': True,
                'validate_certs': True,
                'ca_cert_path': None,
            }
        ]

    raise ValueError(f'Unknown certificate type: {cert_type}')


def _print_server_health(results: dict[str, Any]) -> None:
    for server_hostname, server_data in results.items():
        status = (
            click.style('OK', fg='green')
            if server_data['all_ok']
            else click.style('FAILED', fg='red')
        )
        server_line = f'SERVER {server_hostname} ({server_data["ip"]})'
        print(f'{server_line:<50} {status}')

        for domain, domain_checks in server_data['domains'].items():
            for check_name, check_data in domain_checks.items():
                domain_line = f'  {domain} [{check_name}]'
                if check_data['status'] == 'ok':
                    print(f'{domain_line:<50} {click.style("OK", fg="green")}')
                else:
                    print(
                        f'{domain_line:<50} {click.style("FAILED", fg="red")}\n'
                        f'  {check_data["error"]}'
                    )

        print()


def _uploaded_cert_path(cert: dict[str, Any]) -> str | None:
    cert_path = cert.get('resolved_cert_path') or cert.get('cert_path')
    if not cert_path:
        return None

    path = Path(cert_path)
    return str(path) if path.is_file() else None
