"""
Round-Robin DNS Bypass for Health Checking

Check individual servers behind round-robin DNS by connecting directly to specific
IP addresses while maintaining proper HTTPS/TLS.

Example:
    pycurl_status('https://api.example.com/health', '192.168.1.101')
    200

    pycurl_get('https://api.example.com/data', '192.168.1.102')
    '{"status": "ok"}'

How it works:
    Overrides DNS resolution to connect to a specific IP while using the correct
    hostname for TLS/SNI. This lets you bypass round-robin to test individual servers.
"""

from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import pycurl


def pycurl_status(url: str, target_ip: str) -> int:
    """
    Check HTTP status of a specific server behind round-robin DNS.

    Makes a HEAD request to the target IP while using the hostname for HTTPS/SNI.

    Args:
        url: Full URL to request (e.g., 'https://api.example.com/health')
        target_ip: IP address of specific server (e.g., '192.168.1.101')

    Returns:
        HTTP status code (e.g., 200, 404, 500)
    """
    parsed = urlparse(url)
    hostname = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == 'https' else 80)

    c = pycurl.Curl()
    c.setopt(c.URL, url)

    if Path('/etc/ssl/certs/ca-certificates.crt').exists():
        c.setopt(c.CAINFO, '/etc/ssl/certs/ca-certificates.crt')

    # Override DNS: map hostname:port -> target_ip
    c.setopt(c.RESOLVE, [f'{hostname}:{port}:{target_ip}'])
    c.setopt(c.NOBODY, True)  # HEAD request
    c.setopt(c.TIMEOUT, 5)
    c.perform()
    status_code = c.getinfo(c.RESPONSE_CODE)
    c.close()

    return status_code


def pycurl_get(url: str, target_ip: str, binary: bool = False) -> str | bytes:
    """
    Fetch content from a specific server behind round-robin DNS.

    Makes a GET request to the target IP while using the hostname for HTTPS/SNI.

    Args:
        url: Full URL to request (e.g., 'https://api.example.com/data')
        target_ip: IP address of specific server (e.g., '192.168.1.101')
        binary: If True, return bytes; if False, decode as UTF-8 string

    Returns:
        Response body as UTF-8 string (binary=False) or bytes (binary=True)

    Raises:
        ValueError: If status code is not 200
    """
    parsed = urlparse(url)
    hostname = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == 'https' else 80)

    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)

    if Path('/etc/ssl/certs/ca-certificates.crt').exists():
        c.setopt(c.CAINFO, '/etc/ssl/certs/ca-certificates.crt')

    c.setopt(c.RESOLVE, [f'{hostname}:{port}:{target_ip}'])
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.TIMEOUT, 5)
    c.perform()
    status_code = c.getinfo(c.RESPONSE_CODE)
    c.close()

    if status_code != 200:
        raise ValueError(f'status code: {status_code}')

    body = buffer.getvalue()
    return body if binary else body.decode('utf-8')
