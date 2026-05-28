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
    hostname for TLS/SNI. Certificate validation is configurable.
"""

from io import BytesIO
from urllib.parse import urlparse

import pycurl


USER_AGENT = 'OpenFreeMap health check'
CONNECT_TIMEOUT_SECONDS = 3
REQUEST_TIMEOUT_SECONDS = 8


def pycurl_status(
    url: str,
    target_ip: str | None = None,
    *,
    validate_certs: bool = True,
    ca_cert_path: str | None = None,
) -> int:
    """
    Check HTTP status of a specific server behind round-robin DNS.

    Makes a HEAD request to the target IP while using the hostname for HTTPS/SNI.
    Certificate validation is enabled by default and can use a custom CA/cert file.

    Args:
        url: Full URL to request (e.g., 'https://api.example.com/health')
        target_ip: Optional IP address of specific server (e.g., '192.168.1.101')

    Returns:
        HTTP status code (e.g., 200, 404, 500)
    """
    parsed = urlparse(url)
    hostname = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == 'https' else 80)

    c = pycurl.Curl()
    c.setopt(pycurl.URL, url)
    c.setopt(pycurl.USERAGENT, USER_AGENT)
    c.setopt(pycurl.SSL_VERIFYPEER, 1 if validate_certs else 0)
    c.setopt(pycurl.SSL_VERIFYHOST, 2 if validate_certs else 0)
    if ca_cert_path:
        c.setopt(pycurl.CAINFO, ca_cert_path)
    if target_ip:
        c.setopt(pycurl.RESOLVE, [f'{hostname}:{port}:{target_ip}'])
    c.setopt(pycurl.NOBODY, True)  # HEAD request
    c.setopt(pycurl.CONNECTTIMEOUT, CONNECT_TIMEOUT_SECONDS)
    c.setopt(pycurl.TIMEOUT, REQUEST_TIMEOUT_SECONDS)
    c.perform()
    status_code = c.getinfo(pycurl.RESPONSE_CODE)
    c.close()

    return status_code


def pycurl_get(
    url: str,
    target_ip: str | None = None,
    binary: bool = False,
    *,
    validate_certs: bool = True,
    ca_cert_path: str | None = None,
) -> str | bytes:
    """
    Fetch content from a specific server behind round-robin DNS.

    Makes a GET request to the target IP while using the hostname for HTTPS/SNI.
    Certificate validation is enabled by default and can use a custom CA/cert file.

    Args:
        url: Full URL to request (e.g., 'https://api.example.com/data')
        target_ip: Optional IP address of specific server (e.g., '192.168.1.101')
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
    c.setopt(pycurl.URL, url)
    c.setopt(pycurl.USERAGENT, USER_AGENT)
    c.setopt(pycurl.SSL_VERIFYPEER, 1 if validate_certs else 0)
    c.setopt(pycurl.SSL_VERIFYHOST, 2 if validate_certs else 0)
    if ca_cert_path:
        c.setopt(pycurl.CAINFO, ca_cert_path)
    if target_ip:
        c.setopt(pycurl.RESOLVE, [f'{hostname}:{port}:{target_ip}'])
    c.setopt(pycurl.WRITEDATA, buffer)
    c.setopt(pycurl.CONNECTTIMEOUT, CONNECT_TIMEOUT_SECONDS)
    c.setopt(pycurl.TIMEOUT, REQUEST_TIMEOUT_SECONDS)
    c.perform()
    status_code = c.getinfo(pycurl.RESPONSE_CODE)
    c.close()

    if status_code != 200:
        raise ValueError(f'status code: {status_code}')

    body = buffer.getvalue()
    return body if binary else body.decode('utf-8')
