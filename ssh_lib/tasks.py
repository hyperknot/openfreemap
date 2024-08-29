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
from ssh_lib.kernel import kernel_tweaks_ofm
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


def prepare_tile_gen(c):
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

    c.sudo('mkdir -p /data/ofm/tile_gen/logs')

    c.sudo('chown ofm:ofm /data/ofm/tile_gen/{,*}')
    c.sudo(f'chown ofm:ofm -R {TILE_GEN_BIN}')

    put(c, MODULES_DIR / 'tile_gen' / 'cron.d' / 'ofm_tile_gen', '/etc/cron.d/')


def upload_http_host_config(c):
    domain_le = dotenv_val('DOMAIN_LE').lower()
    domain_ledns = dotenv_val('DOMAIN_LEDNS').lower()
    skip_planet = dotenv_val('SKIP_PLANET').lower() == 'true'
    le_email = dotenv_val('LE_EMAIL').lower()

    if not (domain_le or domain_ledns):
        sys.exit('Please specify DOMAIN_LE or DOMAIN_LEDNS in config/.env')

    if domain_le and not le_email:
        sys.exit('Please add your email to LE_EMAIL when using DOMAIN_LE')

    host_config = {
        'domain_le': domain_le,
        'domain_ledns': domain_ledns,
        'skip_planet': skip_planet,
        'le_email': le_email,
    }

    host_config_str = json.dumps(host_config, indent=2, ensure_ascii=False)
    print(host_config_str)
    put_str(c, '/data/ofm/config/http_host.json', host_config_str)

    if domain_ledns:
        assert (CONFIG_DIR / 'rclone.conf').exists()
        put(
            c,
            CONFIG_DIR / 'rclone.conf',
            f'{REMOTE_CONFIG}/rclone.conf',
            permissions=400,
        )
        put(c, MODULES_DIR / 'http_host' / 'cron.d' / 'ofm_ledns_reader', '/etc/cron.d/')


def prepare_http_host(c):
    kernel_tweaks_ofm(c)

    nginx(c)
    certbot(c)

    c.sudo('rm -rf /data/ofm/http_host/logs')
    c.sudo('mkdir -p /data/ofm/http_host/logs')
    c.sudo('chown ofm:ofm /data/ofm/http_host/logs')

    c.sudo('rm -rf /data/ofm/http_host/logs_nginx')
    c.sudo('mkdir -p /data/ofm/http_host/logs_nginx')
    c.sudo('chown nginx:nginx /data/ofm/http_host/logs_nginx')

    upload_http_host_files(c)
    upload_certificates(c)

    c.sudo(f'{VENV_BIN}/pip install -e {HTTP_HOST_BIN} --use-pep517')


def run_http_host_sync(c):
    print('Running host_manager.py sync --force')
    sudo_cmd(c, f'{VENV_BIN}/python -u {HTTP_HOST_BIN}/host_manager.py sync --force')


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


def upload_certificates(c):
    put_dir(c, CONFIG_DIR / 'certs', '/data/nginx/certs', file_permissions=400)
    c.sudo('chown -R nginx:nginx /data/nginx')


def install_benchmark(c):
    """
    Read docs/quick_notes/http_benchmark.md
    """
    c1000k(c)
    wrk(c)


def setup_ledns_writer(c):
    le_email = dotenv_val('LE_EMAIL').lower()
    domain_ledns = dotenv_val('DOMAIN_LEDNS').lower()
    assert le_email
    assert domain_ledns
    assert (CONFIG_DIR / 'rclone.conf').exists()
    assert (CONFIG_DIR / 'cloudflare.ini').exists()

    rclone(c)
    certbot(c)

    c.sudo(f'mkdir -p {REMOTE_CONFIG}')

    put(
        c,
        CONFIG_DIR / 'rclone.conf',
        f'{REMOTE_CONFIG}/rclone.conf',
        permissions=400,
    )

    put(
        c,
        CONFIG_DIR / 'cloudflare.ini',
        f'{REMOTE_CONFIG}/cloudflare.ini',
        permissions=400,
    )

    c.sudo('rm -rf /data/ofm/ledns')

    put(
        c,
        MODULES_DIR / 'ledns' / 'rclone_write.sh',
        '/data/ofm/ledns/rclone_write.sh',
        create_parent_dir=True,
        permissions=500,
    )

    # only use with --staging
    # c.sudo('certbot delete --noninteractive --cert-name ofm_ledns', warn=True)

    sudo_cmd(
        c,
        'certbot certonly '
        '--dns-cloudflare '
        f'--dns-cloudflare-credentials {REMOTE_CONFIG}/cloudflare.ini '
        '--dns-cloudflare-propagation-seconds 20 '
        f'--noninteractive '
        f'-m {le_email} '
        f'--agree-tos '
        f'--cert-name=ofm_ledns '
        f'--deploy-hook /data/ofm/ledns/rclone_write.sh '
        f'-d {domain_ledns}',
        # f'-d {domain2_ledns}',
        # f'-d {domain2_ledns}',
    )


def setup_loadbalancer(c):
    domain_ledns = dotenv_val('DOMAIN_LEDNS').lower()
    http_host_list = [h.strip() for h in dotenv_val('HTTP_HOST_LIST').split(',') if h.strip()]
    assert (CONFIG_DIR / 'cloudflare.ini').exists()

    config = {
        'domain_ledns': domain_ledns,
        'http_host_list': http_host_list,
        'telegram_token': dotenv_val('TELEGRAM_TOKEN'),
        'telegram_chat_id': dotenv_val('TELEGRAM_CHAT_ID'),
    }

    config_str = json.dumps(config, indent=2, ensure_ascii=False)
    # print(config_str)
    put_str(c, f'{REMOTE_CONFIG}/loadbalancer.json', config_str)

    put(
        c,
        CONFIG_DIR / 'cloudflare.ini',
        f'{REMOTE_CONFIG}/cloudflare.ini',
        permissions=400,
    )

    c.sudo('rm -rf /data/ofm/loadbalancer')
    put_dir(c, MODULES_DIR / 'loadbalancer', '/data/ofm/loadbalancer')
    put_dir(
        c,
        MODULES_DIR / 'loadbalancer' / 'loadbalancer_lib',
        '/data/ofm/loadbalancer/loadbalancer_lib',
    )

    c.sudo(f'{VENV_BIN}/pip install -e /data/ofm/loadbalancer --use-pep517')

    c.sudo('mkdir -p /data/ofm/loadbalancer/logs')
    put(c, MODULES_DIR / 'loadbalancer' / 'cron.d' / 'ofm_loadbalancer', '/etc/cron.d/')

    c.sudo('chown -R ofm:ofm /data/ofm/loadbalancer')
