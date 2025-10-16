import os
import secrets
import socket
import string
import sys
from pathlib import Path

import requests
from fabric import Connection
from invoke import UnexpectedExit


def put(
    c, local_path, remote_path, permissions=None, user='root', group=None, create_parent_dir=False
):
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
    c,
    local_dir: Path,
    remote_dir,
    dir_permissions=None,
    file_permissions=None,
    user='root',
    group=None,
    exclude_set=None,
):
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


def put_str(c, remote_path, str_, create_parent_dir=False):
    tmp_file = 'tmp.txt'
    with open(tmp_file, 'w') as outfile:
        outfile.write(str_ + '\n')
    put(c, tmp_file, remote_path, create_parent_dir=create_parent_dir)
    os.remove(tmp_file)


def file_contains(c, file_path, search_str):
    """Check if a file contains a specific string."""
    if not exists(c, file_path):
        return False

    # Use grep -qF for fixed string search (no regex interpretation)
    # -q for quiet (no output), -F for fixed string
    result = c.sudo(f"grep -qF '{search_str}' '{file_path}'", warn=True, hide=True)
    return result.ok


def append_str(c, remote_path, str_, check_duplicate=False):
    """Append string to file. If check_duplicate=True, only append if string doesn't exist."""
    if check_duplicate and file_contains(c, remote_path, str_.strip()):
        return False  # String already exists, didn't append

    tmp_path = f'/tmp/fabtmp_{random_string(8)}'
    put_str(c, tmp_path, str_)

    sudo_cmd(c, f"cat '{tmp_path}' >> '{remote_path}'")
    c.sudo(f'rm -f {tmp_path}')
    return True  # Successfully appended


def sudo_cmd(c, cmd, *, user=None):
    cmd = cmd.replace('"', '\\"')

    try:
        c.sudo(f'bash -c "{cmd}"', user=user)
    except UnexpectedExit as e:
        print(f'Command failed: {e.result.command}')
        print(f'Error: {e.result.stderr}')
        sys.exit(1)


def run_nice(c, cmd):
    try:
        c.run(cmd)
    except UnexpectedExit as e:
        print(f'Command failed: {e.result.command}')
        print(f'Error: {e.result.stderr}')
        sys.exit(1)


def set_permission(c, path, *, permissions=None, user=None, group=None):
    if user:
        if not group:
            group = user
        c.sudo(f"chown {user}:{group} '{path}'")

    if permissions:
        c.sudo(f"chmod {permissions} '{path}'")


def reboot(c):
    print('Rebooting')
    try:
        c.sudo('reboot')
    except Exception:
        pass


def exists(c, path):
    return c.sudo(f"test -e '{path}'", hide=True, warn=True).ok


def is_dir(c, path):
    return c.sudo(f"test -d '{path}'", hide=True, warn=True).ok


def random_string(length):
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(length))


def ubuntu_release(c):
    return c.run('lsb_release -rs').stdout.strip()[:2]


def ubuntu_codename(c):
    return c.run('lsb_release -cs').stdout.strip()


def apt_get_update(c):
    c.sudo('apt-get update')


def apt_get_install(c, pkgs, warn=False):
    c.sudo(
        f'DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends {pkgs}',
        warn=warn,
        echo=True,
    )


def apt_get_purge(c, pkgs):
    c.sudo(f'DEBIAN_FRONTEND=noninteractive apt-get purge -y {pkgs}')


def apt_get_autoremove(c):
    c.sudo('DEBIAN_FRONTEND=noninteractive apt-get autoremove -y')


def get_username(c):
    return c.run('whoami').stdout.strip()


def add_user(c, username, passwd=None, uid=None):
    uid_str = f'--uid={uid}' if uid else ''

    # --disabled-password -> ssh-key login only
    c.sudo(f'adduser --disabled-password --gecos "" {uid_str} {username}', warn=True)
    if passwd:
        sudo_cmd(c, f'echo "{username}:{passwd}" | chpasswd')


def remove_user(c, username):
    c.sudo(f'userdel -r {username}', warn=True)
    c.sudo(f'rm -rf /home/{username}')


def enable_sudo(c, username, nopasswd=False):
    c.sudo(f'usermod -aG sudo {username}')
    if nopasswd:
        put_str(c, '/etc/sudoers.d/tmp.', f'{username} ALL=(ALL) NOPASSWD:ALL')
        set_permission(c, '/etc/sudoers.d/tmp.', permissions='440', user='root')
        c.sudo(f'mv /etc/sudoers.d/tmp. /etc/sudoers.d/{username}')


def get_latest_release_github(user, repo):
    url = f'https://api.github.com/repos/{user}/{repo}/releases/latest'
    r = requests.get(url)
    r.raise_for_status()

    data = r.json()
    assert data['tag_name'] == data['name']

    return data['tag_name']


def get_ip_from_ssh_alias(ssh_alias):
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

    # Get the resolved hostname from SSH config
    hostname = conn.host

    # Resolve to IP
    ip_address = socket.gethostbyname(hostname)

    return ip_address
