import shlex
from collections.abc import Iterable
from urllib.parse import urlparse

from fabric import Connection

from .utils import put_str


def setup_apt_repository(
    c: Connection,
    *,
    repo_name: str,
    key_url: str,
    repo_url: str,
    suite: str,
    component: str = 'main',
    arch: str | None = None,
):
    """
    Configure a third-party apt repository using a dedicated keyring and `signed-by`.
    Works on Ubuntu 22.04+ and 24.04+.
    """
    keyring_path = apt_repo_keyring_path(repo_name)
    source_path = apt_repo_source_path(repo_name)
    pin_path = apt_repo_pin_path(repo_name)
    source_options = [f'signed-by={keyring_path}']
    if arch:
        source_options.insert(0, f'arch={arch}')
    source_line = f'deb [{" ".join(source_options)}] {repo_url} {suite} {component}'

    tmp_key_path = f'/tmp/{repo_name}-archive-keyring.key'

    c.sudo('install -d -m 0755 /usr/share/keyrings')
    c.sudo(f"curl -fsSL '{key_url}' -o '{tmp_key_path}'")
    c.sudo(f"gpg --dearmor --yes -o '{keyring_path}' '{tmp_key_path}'")

    c.sudo(f"chown root:root '{keyring_path}'")
    c.sudo(f"chmod 0644 '{keyring_path}'")
    c.sudo(f"rm -f '{tmp_key_path}'")

    put_str(c, source_path, source_line)

    origin_host = _extract_repo_origin_host(repo_url)
    pin_content = f'Package: *\nPin: origin {origin_host}\nPin-Priority: 900'
    put_str(c, pin_path, pin_content)


def apt_get_update(c: Connection) -> None:
    c.sudo('apt-get update')


def apt_get_install(c: Connection, pkgs: str, warn: bool = False) -> None:
    c.sudo(
        f'DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends {pkgs}',
        warn=warn,
        echo=True,
    )


def apt_get_purge(c: Connection, pkgs: str | Iterable[str]) -> None:
    if isinstance(pkgs, str):
        pkg_list = shlex.split(pkgs)
    else:
        pkg_list = [str(pkg) for pkg in pkgs]

    for pkg in pkg_list:
        c.sudo(
            f'DEBIAN_FRONTEND=noninteractive apt-get purge -y {shlex.quote(pkg)}',
            warn=True,
        )


def apt_get_autoremove(c: Connection) -> None:
    c.sudo('DEBIAN_FRONTEND=noninteractive apt-get autoremove -y')


def apt_repo_keyring_path(repo_name: str) -> str:
    return f'/usr/share/keyrings/{repo_name}-archive-keyring.gpg'


def apt_repo_source_path(repo_name: str) -> str:
    return f'/etc/apt/sources.list.d/{repo_name}.list'


def apt_repo_pin_path(repo_name: str) -> str:
    return f'/etc/apt/preferences.d/{repo_name}'


def _extract_repo_origin_host(repo_url: str) -> str:
    host = urlparse(repo_url).hostname
    if host:
        return host
    raise ValueError(f'Could not extract repository host from repo_url: {repo_url!r}')
