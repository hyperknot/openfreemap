from ssh_lib.utils import (
    apt_get_autoremove,
    apt_get_install,
    apt_get_purge,
    apt_get_update,
    sudo_cmd,
)


def pkg_upgrade(c):
    apt_get_update(c)
    c.sudo(
        'DEBIAN_FRONTEND=noninteractive apt-get dist-upgrade -y -o Dpkg::Options::="--force-confold"'
    )


def pkg_clean(c):
    pkg_list = [
        # firewalls
        'ufw',
        'nftables',
        'firewalld',
        'iptables-persistent',
        # bloat
        'ntfs-3g',
        'popularity-contest',
        'landscape*',
        'ubuntu-advantage-tools',
    ]

    apt_get_purge(c, ' '.join(pkg_list))
    apt_get_autoremove(c)
    sudo_cmd(c, 'dpkg --list | grep "^rc" | cut -d " " -f 3 | xargs -r dpkg --purge')
    c.sudo('iptables -L', warn=True)


def pkg_base(c):
    pkg_list = [
        'lsb-release',
        'wget',
        'git',
        #
        'gnupg2',
        'gnupg-agent',
        'ca-certificates',
        'ubuntu-keyring',
        #
        'nload',
        'iftop',
        #
        'python3',
        'python3-venv',
    ]

    apt_get_install(c, ' '.join(pkg_list))
