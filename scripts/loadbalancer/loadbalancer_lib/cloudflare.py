from pprint import pprint

import requests


# docs: https://api.cloudflare.com/


def cloudflare_get(path: str, params: dict, cloudflare_api_token: str):
    headers = {'Authorization': f'Bearer {cloudflare_api_token}'}
    res = requests.get(
        f'https://api.cloudflare.com/client/v4{path}', headers=headers, params=params
    )
    res.raise_for_status()
    data = res.json()
    assert data['success'] is True
    return data


def get_zone_id(domain, cloudflare_api_token: str):
    data = cloudflare_get(
        '/zones', params=dict(name=domain), cloudflare_api_token=cloudflare_api_token
    )
    assert len(data['result']) == 1
    zone_info = data['result'][0]
    return zone_info['id']


def get_dns_records_round_robin(zone_id, cloudflare_api_token: str) -> dict:
    data = cloudflare_get(
        f'/zones/{zone_id}/dns_records',
        params=dict(per_page=5000),
        cloudflare_api_token=cloudflare_api_token,
    )
    records = data['result']

    data = {}

    for r in records:
        if r['type'] != 'A':
            continue

        data.setdefault(r['name'], [])
        data[r['name']].append(dict(content=r['content'], id=r['id']))

    return data


def set_records_round_robin(
    zone_id,
    *,
    name: str,
    host_ip_set: set,
    ttl: int = 1,
    proxied: bool,
    comment: str = None,
    cloudflare_api_token: str,
):
    headers = {'Authorization': f'Bearer {cloudflare_api_token}'}

    dns_records = get_dns_records_round_robin(zone_id, cloudflare_api_token=cloudflare_api_token)
    current_records = dns_records.get(name, [])

    current_ips = {r['content'] for r in current_records}
    if current_ips == host_ip_set:
        print(f'No need to update records: {name} currently set: {sorted(current_ips)}')
        return

    # changing records

    # delete all current records first
    for r in current_records:
        delete_record(zone_id, id_=r['id'], cloudflare_api_token=cloudflare_api_token)

    # create new records
    for ip in host_ip_set:
        print(f'Creating record: {name} {ip}')
        json_data = dict(
            type='A',
            name=name,
            content=ip,
            ttl=ttl,
            proxied=proxied,
            comment=comment,
        )
        res = requests.post(
            f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records',
            headers=headers,
            json=json_data,
        )
        res.raise_for_status()
        data = res.json()
        assert data['success'] is True


def delete_record(zone_id, *, id_: str, cloudflare_api_token: str):
    headers = {'Authorization': f'Bearer {cloudflare_api_token}'}

    print(f'Deleting record: {id_}')
    res = requests.delete(
        f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{id_}',
        headers=headers,
        json={},
    )
    res.raise_for_status()
    data = res.json()
    assert data['success'] is True
