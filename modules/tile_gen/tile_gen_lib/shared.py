import json
from io import BytesIO
from pathlib import Path

import pycurl
import requests


def get_versions_for_area(area: str) -> list:
    r = requests.get('https://btrfs.openfreemap.com/dirs.txt', timeout=30)
    r.raise_for_status()

    versions = [v.split('/')[2] for v in r.text.splitlines() if v.startswith(f'areas/{area}/')]
    return sorted(versions)


def check_host_version(domain, host_ip, area, version):
    # check versioned TileJSON
    url = f'https://{domain}/{area}/{version}'
    tilejson_str = pycurl_get(url, domain, host_ip)
    tilejson = json.loads(tilejson_str)
    tiles_url = tilejson['tiles'][0]
    version_in_tilejson = tiles_url.split('/')[4]
    assert version_in_tilejson == version

    # check actual vector tile
    url = f'https://{domain}/{area}/{version}/14/8529/5975.pbf'
    assert pycurl_status(url, domain, host_ip) == 200


def check_host_latest(domain, host_ip, area, version):
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

    # check style
    url = f'https://{domain}/styles/bright'
    assert pycurl_status(url, domain, host_ip) == 200


# pycurl


def pycurl_status(url, domain, host_ip):
    """
    Uses pycurl to make a HTTPS HEAD request using custom resolving,
    checks if the status code is 200
    """

    c = pycurl.Curl()
    c.setopt(c.URL, url)

    # linux needs CA certs specified manually
    if Path('/etc/ssl/certs/ca-certificates.crt').exists():
        c.setopt(c.CAINFO, '/etc/ssl/certs/ca-certificates.crt')

    c.setopt(c.RESOLVE, [f'{domain}:443:{host_ip}'])
    c.setopt(c.NOBODY, True)
    c.setopt(c.TIMEOUT, 5)
    c.perform()
    status_code = c.getinfo(c.RESPONSE_CODE)
    c.close()

    return status_code


def pycurl_get(url, domain, host_ip):
    """
    Uses pycurl to make a HTTPS GET request using custom resolving,
    checks if the status code is 200, and returns the content.
    """

    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)

    # linux needs CA certs specified manually
    if Path('/etc/ssl/certs/ca-certificates.crt').exists():
        c.setopt(c.CAINFO, '/etc/ssl/certs/ca-certificates.crt')

    c.setopt(c.RESOLVE, [f'{domain}:443:{host_ip}'])
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.TIMEOUT, 5)
    c.perform()
    status_code = c.getinfo(c.RESPONSE_CODE)
    c.close()

    if status_code != 200:
        raise ValueError(f'status code: {status_code}')

    return buffer.getvalue().decode('utf8')
