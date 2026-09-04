from pathlib import Path

from fabric import Connection

from .apt import apt_get_install, apt_get_update, setup_apt_repository
from .utils import exists, put, ubuntu_codename


NGINX_REPO_NAME = 'nginx'


def deploy_nginx_base_config(c: Connection, assets_dir: str | Path) -> None:
    update_nginx_packages(c)

    c.sudo('mkdir -p /data/nginx/config /data/nginx/logs /data/nginx/sites /data/nginx/acme')
    c.sudo('chown -R nginx:nginx /data/nginx/acme')
    ensure_self_signed_cert(c)

    assets_dir = Path(assets_dir)
    put(c, assets_dir / 'nginx.conf', '/etc/nginx/nginx.conf')
    put(c, assets_dir / 'mime.types', '/etc/nginx/mime.types')
    put(c, assets_dir / 'default_disable.conf', '/data/nginx/sites/default_disable.conf')
    put(c, assets_dir / 'cloudflare.conf', '/data/nginx/config/cloudflare.conf')

    c.sudo('nginx -t')
    c.sudo('systemctl restart nginx')


def update_nginx_packages(c: Connection) -> None:
    setup_apt_repository(
        c,
        repo_name=NGINX_REPO_NAME,
        key_url='https://nginx.org/keys/nginx_signing.key',
        repo_url='https://nginx.org/packages/mainline/ubuntu',
        suite=ubuntu_codename(c),
        component='nginx',
    )

    apt_get_update(c, NGINX_REPO_NAME)
    apt_get_install(c, 'nginx nginx-module-acme')


def ensure_self_signed_cert(c: Connection) -> None:
    if exists(c, '/etc/nginx/ssl/self_signed.cert'):
        return

    c.sudo('mkdir -p /etc/nginx/ssl')
    c.sudo(
        'openssl req -x509 -nodes -days 3650 -newkey rsa:2048 '
        + '-keyout /etc/nginx/ssl/self_signed.key -out /etc/nginx/ssl/self_signed.cert '
        + '-subj "/C=US/ST=Dummy/L=Dummy/O=Dummy/CN=example.com"',
        hide=True,
    )
