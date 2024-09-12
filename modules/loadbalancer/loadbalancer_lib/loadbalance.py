from datetime import datetime, timedelta, timezone

from loadbalancer_lib.cloudflare import get_zone_id, set_records_round_robin
from loadbalancer_lib.config import config
from loadbalancer_lib.shared import check_host_latest, check_host_version, get_deployed_version
from loadbalancer_lib.telegram_ import telegram_send_message


def check_or_fix(fix=False):
    if not config.http_host_list:
        telegram_quick(
            'OFM loadbalancer no hosts found on list, terminating',
        )
        return

    try:
        results_by_ip = {}
        working_hosts = set()

        for area in config.areas:
            results = run_area(area)
            for host_ip, host_is_ok in results.items():
                results_by_ip.setdefault(host_ip, True)
                results_by_ip[host_ip] &= host_is_ok

        for host_ip, host_is_ok in results_by_ip.items():
            if not host_is_ok:
                telegram_quick(f'OFM loadbalancer ERROR with host: {host_ip}')
            else:
                working_hosts.add(host_ip)

    except Exception as e:
        telegram_quick(f'OFM loadbalancer ERROR with loadbalancer: {e}')
        return

    print(f'working hosts: {sorted(working_hosts)}')

    if fix:
        # if no hosts are detected working, probably a bug in this script
        # fail-safe to include all hosts
        if not working_hosts:
            working_hosts = set(config.http_host_list)
            telegram_quick('OFM loadbalancer FIX found no working hosts, reverting to full list!')

        updated = update_records(working_hosts)
        if updated:
            telegram_quick(f'OFM loadbalancer FIX modified records, new records: {working_hosts}')


def run_area(area):
    deployed_data = get_deployed_version(area)
    version = deployed_data['version']
    last_modified = deployed_data['last_modified']

    if not version:
        print(f'  deployed version not found: {area}')
        return

    print(f'  deployed version {area}: {version}')

    # using relaxed mode for while the servers are still deploying
    now = datetime.now(timezone.utc)
    relaxed_mode = last_modified > now - timedelta(minutes=2)

    results = {}

    for host_ip in config.http_host_list:
        try:
            # don't check latest
            if relaxed_mode:
                print('using relaxed mode')
                check_host_version(config.domain_ledns, host_ip, area, version)
            else:
                check_host_latest(config.domain_ledns, host_ip, area, version)

            results[host_ip] = True
        except Exception as e:
            results[host_ip] = False
            print(e)

    return results


def update_records(working_hosts) -> bool:
    zone_id = get_zone_id(config.domain_root, cloudflare_api_token=config.cloudflare_api_token)

    updated = False

    updated |= set_records_round_robin(
        zone_id=zone_id,
        name=config.domain_ledns,
        host_ip_set=working_hosts,
        proxied=False,
        ttl=300,
        comment='domain_ledns',
        cloudflare_api_token=config.cloudflare_api_token,
    )

    return updated


def telegram_quick(message):
    telegram_send_message(message, config.telegram_token, config.telegram_chat_id)
