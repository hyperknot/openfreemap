from openfreemaps.config import templates
from openfreemaps.utils import (
    apt_get_install,
    apt_get_purge,
    apt_get_update,
    exists,
    put,
    put_str,
    sudo_cmd,
    ubuntu_codename,
)


def nginx(c):
    codename = ubuntu_codename(c)

    if not exists(c, '/usr/sbin/nginx'):
        put_str(
            c,
            '/etc/apt/sources.list.d/nginx.list',
            f'deb http://nginx.org/packages/mainline/ubuntu {codename} nginx',
        )
        sudo_cmd(
            c,
            'wget --quiet -O - http://nginx.org/keys/nginx_signing.key | apt-key add -',
        )
        apt_get_update(c)
        apt_get_install(c, 'nginx')

    c.sudo('rm -rf /data/nginx/config')
    c.sudo('mkdir -p /data/nginx/config')

    c.sudo('rm -rf /data/nginx/logs')
    c.sudo('mkdir -p /data/nginx/logs')

    c.sudo('mkdir -p /data/nginx/sites')

    if not exists(c, '/etc/nginx/ssl/dummy.crt'):
        c.sudo('mkdir -p /etc/nginx/ssl')
        c.sudo(
            'openssl req -x509 -nodes -days 365 -newkey rsa:2048 '
            '-keyout /etc/nginx/ssl/dummy.key -out /etc/nginx/ssl/dummy.crt '
            '-subj "/C=US/ST=Dummy/L=Dummy/O=Dummy/CN=example.com"'
        )

    put(c, f'{templates}/nginx/nginx.conf', '/etc/nginx/')
    put(c, f'{templates}/nginx/default_disable.conf', '/data/nginx/sites')

    c.sudo('service nginx restart')


def certbot(c):
    # https://certbot.eff.org/lets-encrypt/ubuntubionic-nginx
    apt_get_install(c, 'snapd')
    c.run('snap install core', warn=True)
    c.run('snap refresh core', warn=True)

    apt_get_purge(c, 'certbot')
    c.run('snap install --classic certbot', warn=True)
    c.run('snap set certbot trust-plugin-with-root=ok')
    c.run('snap install certbot-dns-cloudflare')
