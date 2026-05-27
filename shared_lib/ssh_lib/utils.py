import fnmatch
import os
import secrets
import shlex
import socket
import string
import sys
import tarfile
import tempfile
from collections.abc import Iterable
from pathlib import Path

from fabric import Connection
from invoke.exceptions import UnexpectedExit


def put(
    c: Connection,
    local_path: str | Path,
    remote_path: str,
    permissions: str | int | None = None,
    user: str = 'root',
    group: str | None = None,
    create_parent_dir: bool = False,
) -> None:
    tmp_path = f'/tmp/fabtmp_{random_string(8)}'
    c.put(local_path, tmp_path)

    if create_parent_dir:
        dirname = os.path.dirname(remote_path)
        c.sudo(f'mkdir -p {dirname}')
        set_permission(c, dirname, user=user, group=group)

    if is_dir(c, remote_path):
        if not remote_path.endswith('/'):
            remote_path += '/'

        filename = os.path.basename(local_path)
        remote_path += filename

    c.sudo(f"mv '{tmp_path}' '{remote_path}'")
    c.sudo(f"rm -rf '{tmp_path}'")

    set_permission(c, remote_path, permissions=permissions, user=user, group=group)


def put_dir(
    c: Connection,
    local_dir: Path,
    remote_dir: str,
    dir_permissions: str | int | None = None,
    file_permissions: str | int | None = None,
    user: str = 'root',
    group: str | None = None,
    exclude_set: set[str] | None = None,
) -> None:
    """
    copies all files from local path to remote path
    not recursive
    """

    files = [file for file in local_dir.iterdir() if file.is_file()]

    if exclude_set:
        files = [f for f in files if f.name not in exclude_set]

    c.sudo(f'mkdir -p "{remote_dir}"')
    set_permission(c, remote_dir, permissions=dir_permissions, user=user, group=group)

    for file in files:
        print(f'uploading {remote_dir}/{file.name}')
        put(c, file, f'{remote_dir}/{file.name}', file_permissions, user, group)


def put_dir_tarball(
    c: Connection,
    local_dir: Path,
    remote_dir: str | Path,
    dir_permissions: str | int | None = None,
    file_permissions: str | int | None = None,
    user: str = 'root',
    group: str | None = None,
    exclude_patterns: Iterable[str] | None = None,
) -> None:
    local_dir = local_dir.resolve()
    remote_dir = str(remote_dir)
    exclude_patterns = {pattern.strip() for pattern in exclude_patterns or () if pattern.strip()}
    root_patterns = {pattern.strip('/') for pattern in exclude_patterns if '/' in pattern}
    component_patterns = {pattern for pattern in exclude_patterns if '/' not in pattern}

    def include(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo | None:
        relative_parts = Path(tarinfo.name).parts[1:]
        if not relative_parts:
            return tarinfo

        path = Path(*relative_parts).as_posix()

        for pattern in root_patterns:
            if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(path, f'{pattern}/*'):
                return None

        for pattern in component_patterns:
            if any(fnmatch.fnmatch(part, pattern) for part in relative_parts):
                return None

        return tarinfo

    with tempfile.NamedTemporaryFile(suffix='.tar.gz') as archive:
        with tarfile.open(archive.name, 'w:gz') as tar:
            tar.add(local_dir, arcname=local_dir.name, filter=include)
        archive.flush()

        tmp_path = f'/tmp/source_{random_string(8)}.tar.gz'
        c.put(archive.name, tmp_path)

    c.sudo(f'rm -rf {shlex.quote(remote_dir)}')
    c.sudo(f'mkdir -p {shlex.quote(remote_dir)}')
    c.sudo(f'tar -xzf {shlex.quote(tmp_path)} -C {shlex.quote(remote_dir)} --strip-components=1')
    c.sudo(f'rm -f {shlex.quote(tmp_path)}')
    set_permission(c, remote_dir, permissions=dir_permissions, user=user, group=group)

    if user:
        group = group or user
        c.sudo(f'chown -R {shlex.quote(user)}:{shlex.quote(group)} {shlex.quote(remote_dir)}')

    if file_permissions:
        c.sudo(
            f'find {shlex.quote(remote_dir)} -type f -exec chmod {shlex.quote(str(file_permissions))} {{}} +'
        )


def put_str(c: Connection, remote_path: str, str_: str, create_parent_dir: bool = False) -> None:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt') as f:
        f.write(str_ + '\n')
        f.flush()
        put(c, f.name, remote_path, create_parent_dir=create_parent_dir)


def file_contains(c: Connection, file_path: str, search_str: str) -> bool:
    """Check if a file contains a specific string."""
    if not exists(c, file_path):
        return False

    # Use grep -qF for fixed string search (no regex interpretation)
    # -q for quiet (no output), -F for fixed string
    result = c.sudo(f"grep -qF '{search_str}' '{file_path}'", warn=True, hide=True)
    return result.ok


def append_str(c: Connection, remote_path: str, str_: str, check_duplicate: bool = False) -> bool:
    """Append string to file. If check_duplicate=True, only append if string doesn't exist."""
    if check_duplicate and file_contains(c, remote_path, str_.strip()):
        return False  # String already exists, didn't append

    tmp_path = f'/tmp/fabtmp_{random_string(8)}'
    put_str(c, tmp_path, str_)

    sudo_cmd(c, f"cat '{tmp_path}' >> '{remote_path}'")
    c.sudo(f'rm -f {tmp_path}')
    return True  # Successfully appended


def sudo_cmd(
    c: Connection, cmd: str, *, user: str | None = None, cwd: str | Path | None = None
) -> None:
    if cwd:
        cmd = f'cd {shlex.quote(str(cwd))} && {cmd}'

    try:
        c.sudo(f'bash -lc {shlex.quote(cmd)}', user=user)
    except UnexpectedExit as e:
        print(f'Command failed: {e.result.command}')
        print(f'Error: {e.result.stderr}')
        sys.exit(1)


def run_nice(c: Connection, cmd: str) -> None:
    try:
        c.run(cmd)
    except UnexpectedExit as e:
        print(f'Command failed: {e.result.command}')
        print(f'Error: {e.result.stderr}')
        sys.exit(1)


def set_permission(
    c: Connection,
    path: str,
    *,
    permissions: str | int | None = None,
    user: str | None = None,
    group: str | None = None,
) -> None:
    if user:
        if not group:
            group = user
        c.sudo(f"chown {user}:{group} '{path}'")

    if permissions:
        c.sudo(f"chmod {permissions} '{path}'")


def reboot(c: Connection) -> None:
    print('Rebooting')
    try:
        c.sudo('reboot')
    except Exception:
        pass


def exists(c: Connection, path: str) -> bool:
    return c.sudo(f"test -e '{path}'", hide=True, warn=True).ok


def is_dir(c: Connection, path: str) -> bool:
    return c.sudo(f"test -d '{path}'", hide=True, warn=True).ok


def ensure_dirs(c: Connection, *paths: str) -> None:
    quoted = ' '.join(shlex.quote(path) for path in paths if path)
    if quoted:
        c.run(f'mkdir -p {quoted}', echo=True)


def truncate_files_in_dir(c: Connection, path: str) -> None:
    quoted = shlex.quote(path)
    c.run(
        f'mkdir -p {quoted} && find {quoted} -type f -exec truncate -s 0 {{}} +',
        warn=True,
        hide=True,
    )


def random_string(length: int) -> str:
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(length))


def get_arch(c: Connection) -> str:
    return c.run('uname -m', hide=True).stdout.strip()


def ubuntu_release(c: Connection) -> int:
    return int(c.run('lsb_release -rs').stdout.strip()[:2])


def ubuntu_codename(c: Connection) -> str:
    return c.run('lsb_release -cs').stdout.strip()


def get_username(c: Connection) -> str:
    return c.run('whoami').stdout.strip()


def add_user(
    c: Connection, username: str, passwd: str | None = None, uid: int | None = None, *, system: bool
) -> None:
    """Create a user if it doesn't already exist."""
    if c.sudo(f'id -u {username}', hide=True, warn=True).ok:
        print(f'User {username} already exists, skipping.')
        return

    if system:
        c.sudo(f'useradd --system --shell /usr/sbin/nologin --user-group {username}')
    else:
        parts = ['adduser', '--disabled-password', '--gecos ""']
        if uid:
            parts.append(f'--uid={uid}')
        parts.append(username)
        c.sudo(' '.join(parts))

        if passwd:
            c.sudo(f'echo "{username}:{passwd}" | chpasswd')


def remove_user(c: Connection, username: str) -> None:
    c.sudo(f'userdel -r {username}', warn=True)
    c.sudo(f'rm -rf /home/{username}')


def enable_sudo(c: Connection, username: str, nopasswd: bool = False) -> None:
    c.sudo(f'usermod -aG sudo {username}')
    if nopasswd:
        put_str(c, '/etc/sudoers.d/tmp.', f'{username} ALL=(ALL) NOPASSWD:ALL')
        set_permission(c, '/etc/sudoers.d/tmp.', permissions='440', user='root')
        c.sudo(f'mv /etc/sudoers.d/tmp. /etc/sudoers.d/{username}')


def get_latest_release_github(user: str, repo: str) -> str:
    import requests

    url = f'https://api.github.com/repos/{user}/{repo}/releases/latest'
    r = requests.get(url, timeout=30)
    r.raise_for_status()

    data = r.json()
    tag_name = data.get('tag_name')
    if not isinstance(tag_name, str) or not tag_name.strip():
        raise RuntimeError(
            f'GitHub latest release response for {user}/{repo} is missing tag_name: {data!r}'
        )

    return tag_name.strip()


def get_ip_from_ssh_alias(ssh_alias: str) -> str:
    """
    Get IP address from SSH config alias.

    Args:
        ssh_alias: SSH hostname/alias from ~/.ssh/config

    Returns:
        str: IP address

    Raises:
        socket.gaierror: If hostname cannot be resolved
    """

    # Create connection (doesn't actually connect)
    conn = Connection(ssh_alias)

    hostname = f'{conn.host or ""}'
    if not hostname:
        raise RuntimeError(f'Could not resolve hostname for SSH alias {ssh_alias!r}')

    return socket.gethostbyname(hostname)
