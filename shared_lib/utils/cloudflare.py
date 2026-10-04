import requests


class CloudflareError(Exception):
    """Implausible content or aria2 failure from Cloudflare-served files."""


CLOUDFLARE_ERRORS = (requests.RequestException, CloudflareError)
