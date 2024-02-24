from ssh_lib import ASSETS_DIR
from ssh_lib.utils import (
    apt_get_install,
    apt_get_purge,
    apt_get_update,
    exists,
    get_latest_release_github,
    put,
    put_str,
    sudo_cmd,
    ubuntu_codename,
)


def nginx(c):
    codename = ubuntu_codename(c)

    if not exists(c, '/usr/sbin/nginx'):
        sudo_cmd(
            c,
            'curl https://nginx.org/keys/nginx_signing.key '
            '| gpg --dearmor --yes -o /etc/apt/keyrings/nginx.gpg',
        )
        put_str(
            c,
            '/etc/apt/sources.list.d/nginx.list',
            f'deb [signed-by=/etc/apt/keyrings/nginx.gpg] http://nginx.org/packages/mainline/ubuntu {codename} nginx',
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
            '-subj "/C=US/ST=Dummy/L=Dummy/O=Dummy/CN=example.com"',
            hide=True,
        )

    put(c, f'{ASSETS_DIR}/nginx/nginx.conf', '/etc/nginx/')
    put(c, f'{ASSETS_DIR}/nginx/mime.types', '/etc/nginx/')
    put(c, f'{ASSETS_DIR}/nginx/default_disable.conf', '/data/nginx/sites')
    put(c, f'{ASSETS_DIR}/nginx/cloudflare.conf', '/data/nginx/config')

    sudo_cmd(c, 'curl https://ssl-config.mozilla.org/ffdhe2048.txt -o /etc/nginx/ffdhe2048.txt')

    c.sudo('nginx -t')
    c.sudo('service nginx restart')


def certbot(c):
    apt_get_install(c, 'snapd')

    # this is silly, but needs to be run twice
    c.sudo('snap install core', warn=True, echo=True)
    c.sudo('snap install core', warn=True, echo=True)

    c.sudo('snap refresh core', warn=True)

    apt_get_purge(c, 'certbot')
    c.sudo('snap install --classic certbot', warn=True)


def lego(c):
    lego_version = get_latest_release_github('go-acme', 'lego')

    url = f'https://github.com/go-acme/lego/releases/download/{lego_version}/lego_{lego_version}_linux_amd64.tar.gz'

    c.run('rm -rf /tmp/lego*')
    c.run('mkdir -p /tmp/lego')
    c.run(
        f'wget -q "{url}" -O /tmp/lego/out.tar.gz',
    )
    c.run('tar xzvf /tmp/lego/out.tar.gz -C /tmp/lego')
    c.run('chmod +x /tmp/lego/lego')
    c.run('mv /tmp/lego/lego /usr/local/bin')
    c.run('rm -rf /tmp/lego*')

    c.run('mkdir -p /data/nginx/acme-challenges/')
