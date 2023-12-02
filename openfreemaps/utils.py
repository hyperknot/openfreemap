import os
import secrets
import string


def put(c, local_path, remote_path, permissions=None, owner='root', group=None):
    tmp_path = f'/tmp/fabtmp_{random_string(8)}'
    c.put(local_path, tmp_path)

    if is_dir(c, remote_path):
        if not remote_path.endswith('/'):
            remote_path += '/'

        filename = os.path.basename(local_path)
        remote_path += filename

    c.sudo(f"mv '{tmp_path}' '{remote_path}'")
    c.sudo(f"rm -rf '{tmp_path}'")

    set_permission(c, remote_path, permissions, owner, group)


def put_str(c, remote_path, str_):
    tmp_file = 'tmp.txt'
    with open(tmp_file, 'w') as outfile:
        outfile.write(str_ + '\n')
    put(c, tmp_file, remote_path)
    os.remove(tmp_file)


def append_str(c, remote_path, str_):
    tmp_path = f'/tmp/fabtmp_{random_string(8)}'
    put_str(c, tmp_path, str_)

    sudo_cmd(c, f"cat '{tmp_path}' >> '{remote_path}'")
    c.sudo(f'rm -f {tmp_path}')


def sudo_cmd(c, cmd):
    cmd = cmd.replace('"', '\\"')
    c.sudo(f'bash -c "{cmd}"')


def set_permission(c, path, permissions=None, owner=None, group=None):
    if owner:
        if not group:
            group = owner

        c.sudo(f"chown {owner}:{group} '{path}'")

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
    )


def apt_get_purge(c, pkgs):
    c.sudo(f'DEBIAN_FRONTEND=noninteractive apt-get purge -y {pkgs}')


def apt_get_autoremove(c):
    c.sudo('DEBIAN_FRONTEND=noninteractive apt-get autoremove -y')


def get_username(c):
    return c.run('whoami').stdout.strip()
