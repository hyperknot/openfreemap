#!/usr/bin/env python3
import datetime
import json

import click
import requests
from dotenv import dotenv_values
from loadbalancer_lib.cloudflare import get_zone_id, set_records_round_robin
from loadbalancer_lib.curl import pycurl_get, pycurl_status
from loadbalancer_lib.telegram_ import telegram_send_message


AREAS = ['planet', 'monaco']


@click.group()
def cli():
    """
    Manages load-balancing of Round-Robin DNS records
    """


@cli.command()
def check():
    """
    Runs load-balancing check (triggered by cron every minute)
    """

    print(f'starting loadbalancer check at: {datetime.datetime.now(tz=datetime.timezone.utc)}')
    check_or_fix(fix=False)


@cli.command()
def fix():
    """
    Fixes records based on check results
    """

    print(f'starting loadbalancer fix at: {datetime.datetime.now(tz=datetime.timezone.utc)}')
    check_or_fix(fix=True)


def check_or_fix(fix=False):
    with open('/data/ofm/config/loadbalancer.json') as fp:
        c = json.load(fp)
        # print(c)

    try:
        results_by_ip = {}
        working_hosts = set()

        for area in AREAS:
            for host_ip, host_is_ok in run_area(c, area).items():
                results_by_ip.setdefault(host_ip, True)
                results_by_ip[host_ip] &= host_is_ok

        for host_ip, host_is_ok in results_by_ip.items():
            if not host_is_ok:
                message = f'OFM ERROR with host: {host_ip}'
                print(message)
                telegram_send_message(message, c['telegram_token'], c['telegram_chat_id'])
            else:
                working_hosts.add(host_ip)

    except Exception as e:
        message = f'OFM ERROR with loadbalancer: {e}'
        print(message)
        telegram_send_message(message, c['telegram_token'], c['telegram_chat_id'])
        return

    print(f'working hosts: {sorted(working_hosts)}')

    if fix:
        # if no hosts are detected working, probably a bug in this script
        # fail-safe to include all hosts
        if not working_hosts:
            working_hosts = set(c['http_host_list'])

            message = 'OFM loadbalancer FIX found no working hosts, reverting to full list!'
            print(message)
            telegram_send_message(message, c['telegram_token'], c['telegram_chat_id'])

        updated = update_records(c, working_hosts)
        if updated:
            message = f'OFM loadbalancer FIX modified records, new records: {working_hosts}'
            print(message)
            telegram_send_message(message, c['telegram_token'], c['telegram_chat_id'])


def run_area(c, area):
    target_version = get_target_version(area)

    print(f'target version: {area}: {target_version}')

    results = {}

    for host_ip in c['http_host_list']:
        try:
            check_host(c['domain_ledns'], host_ip, area, target_version)
            results[host_ip] = True
        except Exception:
            results[host_ip] = False

    return results


def check_host(domain, host_ip, area, version):
    # check TileJSON first
    url = f'https://{domain}/{area}'
    tilejson_str = pycurl_get(url, domain, host_ip)
    tilejson = json.loads(tilejson_str)
    tiles_url = tilejson['tiles'][0]
    version_in_tilejson = tiles_url.split('/')[4]
    assert version_in_tilejson == version

    # check actual vector tile
    url = f'https://{domain}/{area}/{version}/14/8529/5975.pbf'
    assert pycurl_status(url, domain, host_ip) == 200


def get_target_version(area):
    url = f'https://assets.openfreemap.com/versions/deployed_{area}.txt'
    response = requests.get(url)
    response.raise_for_status()
    return response.text.strip()


def update_records(c, working_hosts) -> bool:
    config = dotenv_values('/data/ofm/config/cloudflare.ini')
    cloudflare_api_token = config['dns_cloudflare_api_token']

    domain = '.'.join(c['domain_ledns'].split('.')[-2:])
    zone_id = get_zone_id(domain, cloudflare_api_token=cloudflare_api_token)

    updated = False

    updated |= set_records_round_robin(
        zone_id=zone_id,
        name=c['domain_ledns'],
        host_ip_set=working_hosts,
        proxied=False,
        ttl=300,
        comment='domain_ledns',
        cloudflare_api_token=cloudflare_api_token,
    )

    updated |= set_records_round_robin(
        zone_id=zone_id,
        name=c['domain_cf'],
        host_ip_set=working_hosts,
        proxied=True,
        comment='domain_cf',
        cloudflare_api_token=cloudflare_api_token,
    )

    return updated


if __name__ == '__main__':
    cli()
