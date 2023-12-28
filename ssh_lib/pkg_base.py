from ssh_lib.utils import (
    apt_get_install,
    apt_get_update,
)


def pkg_base(c):
    pkg_list = [
        'lsb-release',
        'wget',
        'git',
        'build-essential',
        'unzip',
        'rsync',
        'btrfs-progs',
        'pigz',
        'aria2',
        #
        'gnupg2',
        'gnupg-agent',
        'ca-certificates',
        'ubuntu-keyring',
        #
        'nload',
        'iftop',
        'vnstat',
        #
        'python3',
        'python3-venv',
    ]

    apt_get_install(c, ' '.join(pkg_list))


def pkg_upgrade(c):
    apt_get_update(c)
    c.sudo(
        'DEBIAN_FRONTEND=noninteractive apt-get dist-upgrade -y -o Dpkg::Options::="--force-confold"'
    )
