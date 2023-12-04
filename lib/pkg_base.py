from lib.utils import (
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
    clean_list = [
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

    apt_get_purge(c, ' '.join(clean_list))
    apt_get_autoremove(c)
    sudo_cmd(c, 'dpkg --list | grep "^rc" | cut -d " " -f 3 | xargs -r dpkg --purge')
    c.sudo('iptables -L')


def pkg_base(c):
    apt_get_install(c, 'nload iftop')
