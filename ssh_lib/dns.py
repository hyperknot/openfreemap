import time

from ssh_lib.utils import apt_get_purge, exists, put_str


def setup_dns(c):
    if exists(c, '/etc/network/interfaces'):
        c.sudo("sed -i '/dns-nameservers/d' /etc/network/interfaces")

    apt_get_purge(c, 'resolvconf')
    c.sudo('rm -rf /etc/resolvconf')

    c.sudo('systemctl stop systemd-resolved')
    c.sudo('systemctl disable systemd-resolved')

    print('chattr -i')
    c.sudo('chattr -i /etc/resolv.conf', warn=True)
    c.sudo('rm -f /etc/resolv.conf')
    put_str(
        c,
        '/etc/resolv.conf',
        'nameserver 1.1.1.1\nnameserver 1.0.0.1\nnameserver 2606:4700:4700::1111\nnameserver 2606:4700:4700::1001',
    )
    time.sleep(1)
    print('chattr +i')
    c.sudo('chattr +i /etc/resolv.conf')

    apt_get_purge(c, 'bind9*')
    c.sudo('rm -rf /var/cache/bind')
