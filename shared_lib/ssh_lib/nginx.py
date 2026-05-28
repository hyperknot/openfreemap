from fabric import Connection

from .apt import (
    apt_get_install,
    apt_get_update,
    setup_apt_repository,
)
from .config import config
from .utils import (
    exists,
    put,
    ubuntu_codename,
)


NGINX_REPO_NAME = 'nginx'
ACME_MODULE_RUNTIME_PATH = '/usr/lib/nginx/modules/ngx_http_acme_module.so'


def nginx(c: Connection) -> None:
    install_nginx(c)

    c.sudo('rm -rf /data/nginx/config')
    c.sudo('mkdir -p /data/nginx/config')

    c.sudo('rm -rf /data/nginx/logs')
    c.sudo('mkdir -p /data/nginx/logs')

    c.sudo('rm -rf /data/nginx/sites')
    c.sudo('mkdir -p /data/nginx/sites')

    # ACME module state (account keys, issued certs, order bookkeeping)
    c.sudo('mkdir -p /data/nginx/acme')
    c.sudo('chown -R nginx:nginx /data/nginx/acme')

    generate_self_signed_cert(c)

    put(c, f'{config.local_assets_dir}/nginx/nginx.conf', '/etc/nginx/')
    put(c, f'{config.local_assets_dir}/nginx/mime.types', '/etc/nginx/')
    put(c, f'{config.local_assets_dir}/nginx/default_disable.conf', '/data/nginx/sites')
    put(c, f'{config.local_assets_dir}/nginx/cloudflare.conf', '/data/nginx/config')

    c.sudo('nginx -t')
    c.sudo('service nginx restart')
    verify_acme_module_after_restart(c)


def install_nginx(c: Connection) -> None:
    if exists(c, '/usr/sbin/nginx'):
        return

    setup_apt_repository(
        c,
        repo_name=NGINX_REPO_NAME,
        key_url='https://nginx.org/keys/nginx_signing.key',
        repo_url='https://nginx.org/packages/mainline/ubuntu',
        suite=ubuntu_codename(c),
        component='nginx',
    )
    apt_get_update(c)
    apt_get_install(c, 'nginx nginx-module-acme')


def verify_acme_module_after_restart(c: Connection) -> None:
    pid_result = c.sudo('cat /run/nginx.pid', warn=True, hide=True)
    if not pid_result.ok:
        raise RuntimeError(f'ACME verify failed on {c.host}. Could not read /run/nginx.pid.')

    pid = pid_result.stdout.strip()
    if not pid.isdigit():
        raise RuntimeError(f'ACME verify failed on {c.host}. Invalid nginx pid: {pid!r}')

    maps_result = c.sudo(f'cat /proc/{pid}/maps', warn=True, hide=True)
    if not maps_result.ok:
        raise RuntimeError(f'ACME verify failed on {c.host}. Could not read /proc/{pid}/maps.')

    if ACME_MODULE_RUNTIME_PATH in maps_result.stdout:
        return

    raise RuntimeError(
        f'ACME verify failed on {c.host}. '
        + f'{ACME_MODULE_RUNTIME_PATH} is not loaded in the running nginx process.'
    )


def generate_self_signed_cert(c: Connection) -> None:
    if exists(c, '/etc/nginx/ssl/self_signed.cert'):
        return

    c.sudo('mkdir -p /etc/nginx/ssl')
    c.sudo(
        'openssl req -x509 -nodes -days 3650 -newkey rsa:2048 '
        + '-keyout /etc/nginx/ssl/self_signed.key -out /etc/nginx/ssl/self_signed.cert '
        + '-subj "/C=US/ST=Dummy/L=Dummy/O=Dummy/CN=example.com"',
        hide=True,
    )
