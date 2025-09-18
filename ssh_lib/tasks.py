import json
import sys

from ssh_lib import (
    CONFIG_DIR,
    HTTP_HOST_BIN,
    MODULES_DIR,
    OFM_DIR,
    REMOTE_CONFIG,
    TILE_GEN_BIN,
    VENV_BIN,
    dotenv_val,
)
from ssh_lib.benchmark import c1000k, wrk
from ssh_lib.kernel import kernel_limits1m, kernel_somaxconn65k
from ssh_lib.nginx import certbot, nginx
from ssh_lib.pkg_base import pkg_base, pkg_upgrade
from ssh_lib.planetiler import install_planetiler
from ssh_lib.rclone import rclone
from ssh_lib.utils import add_user, enable_sudo, put, put_dir, put_str, sudo_cmd


def prepare_shared(c):
    # creates ofm user with uid=2000, disabled password and nopasswd sudo
    add_user(c, 'ofm', uid=2000)
    enable_sudo(c, 'ofm', nopasswd=True)

    pkg_upgrade(c)
    pkg_base(c)
    rclone(c)

    c.sudo(f'mkdir -p {REMOTE_CONFIG}')
    c.sudo(f'chown ofm:ofm {REMOTE_CONFIG}')
    c.sudo(f'chown ofm:ofm {OFM_DIR}')

    upload_config_json(c)

    prepare_venv(c)


def prepare_venv(c):
    put(
        c,
        MODULES_DIR / 'prepare-virtualenv.sh',
        OFM_DIR,
        permissions='755',
        user='ofm',
    )
    sudo_cmd(c, f'cd {OFM_DIR} && source prepare-virtualenv.sh')


def prepare_tile_gen(c, *, enable_cron):
    c.sudo('rm -f /etc/cron.d/ofm_tile_gen')

    install_planetiler(c)

    c.sudo(f'rm -rf {TILE_GEN_BIN}')

    put_dir(c, MODULES_DIR / 'tile_gen', TILE_GEN_BIN, file_permissions='755')

    for dirname in ['tile_gen_lib', 'scripts']:
        put_dir(c, MODULES_DIR / 'tile_gen' / dirname, f'{TILE_GEN_BIN}/{dirname}')

    if (CONFIG_DIR / 'rclone.conf').exists():
        put(
            c,
            CONFIG_DIR / 'rclone.conf',
            f'{REMOTE_CONFIG}/rclone.conf',
            permissions='600',
            user='ofm',
        )

    c.sudo(f'{VENV_BIN}/pip install -e {TILE_GEN_BIN} --use-pep517')

    c.sudo('rm -rf /data/ofm/tile_gen/logs')
    c.sudo('mkdir -p /data/ofm/tile_gen/logs')

    c.sudo('chown ofm:ofm /data/ofm/tile_gen/{,*}')
    c.sudo(f'chown ofm:ofm -R {TILE_GEN_BIN}')

    if enable_cron:
        put(c, MODULES_DIR / 'tile_gen' / 'cron.d' / 'ofm_tile_gen', '/etc/cron.d/')


def prepare_http_host(c):
    kernel_somaxconn65k(c)
    kernel_limits1m(c)

    nginx(c)
    certbot(c)

    c.sudo('rm -rf /data/ofm/http_host/logs')
    c.sudo('mkdir -p /data/ofm/http_host/logs')
    c.sudo('chown ofm:ofm /data/ofm/http_host/logs')

    c.sudo('rm -rf /data/ofm/http_host/logs_nginx')
    c.sudo('mkdir -p /data/ofm/http_host/logs_nginx')
    c.sudo('chown nginx:nginx /data/ofm/http_host/logs_nginx')

    upload_http_host_files(c)

    if dotenv_val('DOMAIN_ROUNDROBIN'):
        assert (CONFIG_DIR / 'rclone.conf').exists()
        put(
            c,
            CONFIG_DIR / 'rclone.conf',
            f'{REMOTE_CONFIG}/rclone.conf',
            permissions=400,
        )
        put(c, MODULES_DIR / 'http_host' / 'cron.d' / 'ofm_roundrobin_reader', '/etc/cron.d/')

    c.sudo(f'{VENV_BIN}/pip install -e {HTTP_HOST_BIN} --use-pep517')


def run_http_host_sync(c):
    print('Running http_host.py sync --force')
    sudo_cmd(c, f'{VENV_BIN}/python -u {HTTP_HOST_BIN}/http_host.py sync --force')


def upload_http_host_files(c):
    c.sudo(f'rm -rf {HTTP_HOST_BIN}')
    c.sudo(f'mkdir -p {HTTP_HOST_BIN}')

    put_dir(c, MODULES_DIR / 'http_host', HTTP_HOST_BIN, file_permissions='755')

    for dirname in ['http_host_lib', 'scripts']:
        put_dir(c, MODULES_DIR / 'http_host' / dirname, f'{HTTP_HOST_BIN}/{dirname}')

    put_dir(
        c,
        MODULES_DIR / 'http_host' / 'http_host_lib' / 'nginx_confs',
        f'{HTTP_HOST_BIN}/http_host_lib/nginx_confs',
    )

    c.sudo('chown -R ofm:ofm /data/ofm/http_host')


def install_benchmark(c):
    """
    Read docs/quick_notes/http_benchmark.md
    """
    c1000k(c)
    wrk(c)


def upload_config_json(c):
    domain_direct = dotenv_val('DOMAIN_DIRECT').lower()
    domain_roundrobin = dotenv_val('DOMAIN_ROUNDROBIN').lower()
    skip_planet = dotenv_val('SKIP_PLANET').lower() == 'true'
    self_signed_certs = dotenv_val('SELF_SIGNED_CERTS').lower() == 'true'
    letsencrypt_email = dotenv_val('LETSENCRYPT_EMAIL').lower()

    if not (domain_direct or domain_roundrobin):
        sys.exit('Please specify DOMAIN_DIRECT or DOMAIN_ROUNDROBIN in config/.env')

    if domain_direct and not letsencrypt_email and not self_signed_certs:
        sys.exit('Please add your email to LETSENCRYPT_EMAIL when using DOMAIN_DIRECT')

    http_host_list = [h.strip() for h in dotenv_val('HTTP_HOST_LIST').split(',') if h.strip()]

    config = {
        'domain_direct': domain_direct,
        'domain_roundrobin': domain_roundrobin,
        'letsencrypt_email': letsencrypt_email,
        'skip_planet': skip_planet,
        'self_signed_certs': self_signed_certs,
        'http_host_list': http_host_list,
        'telegram_token': dotenv_val('TELEGRAM_TOKEN'),
        'telegram_chat_id': dotenv_val('TELEGRAM_CHAT_ID'),
    }

    config_str = json.dumps(config, indent=2, ensure_ascii=False)
    print(config_str)
    put_str(c, f'{REMOTE_CONFIG}/config.json', config_str)


def setup_loadbalancer(c):
    c.sudo('rm -f /etc/cron.d/ofm_loadbalancer')

    c.sudo('rm -rf /data/ofm/loadbalancer')
    put_dir(c, MODULES_DIR / 'loadbalancer', '/data/ofm/loadbalancer')
    put_dir(
        c,
        MODULES_DIR / 'loadbalancer' / 'loadbalancer_lib',
        '/data/ofm/loadbalancer/loadbalancer_lib',
    )

    c.sudo(f'{VENV_BIN}/pip install -e /data/ofm/loadbalancer --use-pep517')

    c.sudo('mkdir -p /data/ofm/loadbalancer/logs')
    c.sudo('chown -R ofm:ofm /data/ofm/loadbalancer')

    put(c, MODULES_DIR / 'loadbalancer' / 'cron.d' / 'ofm_loadbalancer', '/etc/cron.d/')
