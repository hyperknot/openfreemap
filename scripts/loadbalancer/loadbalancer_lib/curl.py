from io import BytesIO

import pycurl


def pycurl_status(url, domain, host_ip):
    """
    Uses pycurl to make a HTTPS HEAD request using custom resolving,
    checks if the status code is 200
    """

    c = pycurl.Curl()
    c.setopt(c.URL, url)
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
    c.setopt(c.CAINFO, '/etc/ssl/certs/ca-certificates.crt')
    c.setopt(c.RESOLVE, [f'{domain}:443:{host_ip}'])
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.TIMEOUT, 5)
    c.perform()
    status_code = c.getinfo(c.RESPONSE_CODE)
    c.close()

    if status_code != 200:
        raise ValueError('non-200')

    return buffer.getvalue().decode('utf8')
