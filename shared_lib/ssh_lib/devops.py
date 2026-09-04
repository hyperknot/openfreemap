import json
import re
import shlex
import urllib.request

from fabric import Connection

from .utils import exists


BORG_BIN = '/usr/local/bin/borg'
BORG_MAJOR = 1
RCLONE_BIN = '/usr/bin/rclone'
UV_BIN = '/usr/local/bin/uv'


def ensure_devops_tools(c: Connection) -> None:
    """Install the standard operational tools when missing."""
    ensure_borg(c)
    ensure_uv(c)
    ensure_rclone(c)


def ensure_borg(c: Connection) -> None:
    if exists(c, BORG_BIN):
        return

    release = _latest_github_release('borgbackup', 'borg', BORG_MAJOR)
    url = (
        f'https://github.com/borgbackup/borg/releases/download/{release}/'
        'borg-linux-glibc235-x86_64-gh'
    )
    c.sudo(f'wget -qO /tmp/borg {shlex.quote(url)}')
    c.sudo(f'install -m 0755 /tmp/borg {BORG_BIN}')
    c.sudo('rm -f /tmp/borg')
    c.run(f'{BORG_BIN} --version')


def ensure_uv(c: Connection) -> None:
    if exists(c, UV_BIN):
        return

    c.sudo(
        'env UV_UNMANAGED_INSTALL=/usr/local/bin sh -c '
        "'curl -LsSf https://astral.sh/uv/install.sh | sh'"
    )
    c.run(f'{UV_BIN} --version')


def ensure_rclone(c: Connection) -> None:
    if exists(c, RCLONE_BIN):
        return

    c.sudo("sh -c 'curl -fsSL --retry 3 --retry-all-errors https://rclone.org/install.sh | bash'")
    c.run(f'{RCLONE_BIN} version')


def _latest_github_release(owner: str, repo: str, major: int) -> str:
    url = f'https://api.github.com/repos/{owner}/{repo}/releases?per_page=100'
    with urllib.request.urlopen(url, timeout=30) as response:
        releases = json.load(response)

    versions = []
    for release in releases:
        tag = release.get('tag_name', '')
        match = re.fullmatch(rf'{major}\.(\d+)\.(\d+)', tag)
        if match and not release.get('draft') and not release.get('prerelease'):
            versions.append(((int(match[1]), int(match[2])), tag))

    if not versions:
        raise RuntimeError(f'Could not find the latest {owner}/{repo} {major}.x release')
    return max(versions)[1]
