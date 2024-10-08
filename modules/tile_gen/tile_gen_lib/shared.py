import json
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import pycurl
import requests


def get_versions_for_area(area: str) -> list:
    """
    Download the files.txt and check for the runs with the "done" file present
    """
    r = requests.get('https://btrfs.openfreemap.com/files.txt', timeout=30)
    r.raise_for_status()

    versions = []

    files = r.text.splitlines()
    for f in files:
        if not f.startswith(f'areas/{area}/'):
            continue
        if not f.endswith('/done'):
            continue
        version_str = f.split('/')[2]
        versions.append(version_str)

    return sorted(versions)


def get_deployed_version(area: str) -> dict:
    r = requests.get(f'https://assets.openfreemap.com/deployed_versions/{area}.txt', timeout=30)
    r.raise_for_status()
    version = r.text.strip()

    last_modified_str = r.headers.get('Last-Modified')
    last_modified = parse_http_last_modified(last_modified_str)

    return dict(
        version=version,
        last_modified=last_modified,
    )


def parse_http_last_modified(date_string) -> datetime:
    parsed_date = datetime.strptime(date_string, '%a, %d %b %Y %H:%M:%S GMT')
    parsed_date = parsed_date.replace(tzinfo=timezone.utc)
    return parsed_date


def check_host_version(domain, host_ip, area, version):
    # check versioned TileJSON
    check_tilejson(f'https://{domain}/{area}/{version}', domain, host_ip, version)

    # check actual vector tile
    url = f'https://{domain}/{area}/{version}/14/8529/5975.pbf'
    assert pycurl_status(url, domain, host_ip) == 200


def check_host_latest(domain, host_ip, area, version):
    # check latest TileJSON
    check_tilejson(f'https://{domain}/{area}', domain, host_ip, version)

    # check versioned TileJSON
    check_tilejson(f'https://{domain}/{area}/{version}', domain, host_ip, version)

    # check actual vector tile
    url = f'https://{domain}/{area}/{version}/14/8529/5975.pbf'
    assert pycurl_status(url, domain, host_ip) == 200

    # check style
    url = f'https://{domain}/styles/bright'
    assert pycurl_status(url, domain, host_ip) == 200


def check_tilejson(url, domain, host_ip, version):
    tilejson_str = pycurl_get(url, domain, host_ip)
    tilejson = json.loads(tilejson_str)
    tiles_url = tilejson['tiles'][0]
    version_in_tilejson = tiles_url.split('/')[4]
    assert version_in_tilejson == version


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
