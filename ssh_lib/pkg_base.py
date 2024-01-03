from ssh_lib.utils import (
    apt_get_install,
    apt_get_update,
)


def pkg_base(c):
    pkg_list = [
        'aria2',
        'build-essential',
        'curl',
        'dnsutils',
        'git',
        'htop',
        'lsb-release',
        'pigz',
        'rsync',
        'unzip',
        'wget',
        'psmisc',
        'util-linux'
        #
        'btrfs-progs',
        #
        'ca-certificates',
        'gnupg-agent',
        'gnupg2',
        'ubuntu-keyring',
        #
        'iftop',
        'nload',
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
