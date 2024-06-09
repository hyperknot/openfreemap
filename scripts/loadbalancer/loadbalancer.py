#!/usr/bin/env python3

import json

import click
import requests
from loadbalancer_lib.curl import pycurl_get, pycurl_status


AREAS = ['planet', 'monaco']


@click.group()
def cli():
    """
    Manages load-balancing of Round-Robin DNS records
    """


@cli.command()
def run():
    """
    Runs load-balancing job (triggered by cron every minute)
    """

    with open('/data/ofm/config/loadbalancer.json') as fp:
        c = json.load(fp)
    print(c)

    try:
        results_by_ip = {}

        for area in AREAS:
            for host_ip, host_ok in run_area(c, area).items():
                results_by_ip.setdefault(host_ip, True)
                results_by_ip[host_ip] &= host_ok

        for host_ip, host_ok in results_by_ip.items():
            if not host_ok:
                print(f'{host_ip} ERROR')
                # TODO send message

    except Exception as e:
        print(e)
        # TODO send message


def run_area(c, area):
    deployed_version = get_deployed_version(area)

    print(f'deployed version: {area}: {deployed_version}')

    results = dict()

    for host_ip in c['load_balance_host_list']:
        try:
            check_host(c['domain_ledns'], host_ip, area, deployed_version)
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


def get_deployed_version(area):
    url = f'https://assets.openfreemap.com/versions/deployed_{area}.txt'
    response = requests.get(url)
    response.raise_for_status()
    return response.text.strip()


if __name__ == '__main__':
    cli()
