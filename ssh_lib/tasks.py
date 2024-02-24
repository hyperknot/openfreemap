import json
import sys

from ssh_lib import (
    CONFIG_DIR,
    HTTP_HOST_BIN,
    OFM_DIR,
    REMOTE_CONFIG,
    SCRIPTS_DIR,
    TILE_GEN_BIN,
    dotenv_val,
)
from ssh_lib.benchmark import c1000k, wrk
from ssh_lib.kernel import kernel_tweaks_ofm
from ssh_lib.nginx import certbot, nginx
from ssh_lib.pkg_base import pkg_base, pkg_upgrade
from ssh_lib.planetiler import planetiler
from ssh_lib.rclone import rclone
from ssh_lib.utils import add_user, enable_sudo, put, put_dir, put_str, sudo_cmd


def prepare_shared(c):
    # creates ofm user with uid=2000, disabled password and nopasswd sudo
    add_user(c, 'ofm', uid=2000)
    enable_sudo(c, 'ofm', nopasswd=True)

    pkg_upgrade(c)
    pkg_base(c)

    kernel_tweaks_ofm(c)

    c.sudo(f'mkdir -p {REMOTE_CONFIG}')
    c.sudo('chown ofm:ofm /data/ofm/config')
    c.sudo('chown ofm:ofm /data/ofm')

    prepare_venv(c)


def prepare_venv(c):
    put(
        c,
        SCRIPTS_DIR / 'prepare-virtualenv.sh',
        OFM_DIR,
        permissions='755',
        user='ofm',
    )
    sudo_cmd(c, f'cd {OFM_DIR} && source prepare-virtualenv.sh')


def prepare_tile_gen(c):
    planetiler(c)
    rclone(c)

    for file in [
        'extract_btrfs.sh',
        'planetiler_monaco.sh',
        'planetiler_planet.sh',
        'cloudflare_index.sh',
        'cloudflare_upload.sh',
    ]:
        put(
            c,
            SCRIPTS_DIR / 'tile_gen' / file,
            TILE_GEN_BIN,
            permissions='755',
        )

    put(
        c,
        SCRIPTS_DIR / 'tile_gen' / 'extract_mbtiles' / 'extract_mbtiles.py',
        f'{TILE_GEN_BIN}/extract_mbtiles/extract_mbtiles.py',
        create_parent_dir=True,
    )

    put(
        c,
        SCRIPTS_DIR / 'tile_gen' / 'shrink_btrfs' / 'shrink_btrfs.py',
        f'{TILE_GEN_BIN}/shrink_btrfs/shrink_btrfs.py',
        create_parent_dir=True,
    )

    if (CONFIG_DIR / 'rclone.conf').exists():
        put(
            c,
            CONFIG_DIR / 'rclone.conf',
            f'{REMOTE_CONFIG}/rclone.conf',
            permissions='600',
            user='ofm',
        )

    c.sudo('chown ofm:ofm /data/ofm/tile_gen')
    c.sudo('chown ofm:ofm -R /data/ofm/tile_gen/bin')


def upload_http_host_config(c):
    domain_le = dotenv_val('DOMAIN_LE').lower()
    domain_cf = dotenv_val('DOMAIN_CF').lower()
    skip_planet = dotenv_val('SKIP_PLANET').lower() == 'true'
    le_email = dotenv_val('LE_EMAIL').lower()

    if not (domain_le or domain_cf):
        sys.exit('Please specify DOMAIN_LE or DOMAIN_CF in config/.env')

    if domain_cf:
        if (
            not (CONFIG_DIR / 'certs' / 'ofm_cf.key').exists()
            or not (CONFIG_DIR / 'certs' / 'ofm_cf.cert').exists()
        ):
            sys.exit(
                'When using DOMAIN_CF, please put ofm_cf.key and ofm_cf.cert files in config/certs'
            )

    if domain_le and not le_email:
        sys.exit('Please add your email to LE_EMAIL when using DOMAIN_LE')

    host_config = {
        'domain_le': domain_le,
        'domain_cf': domain_cf,
        'skip_planet': skip_planet,
        'le_email': le_email,
    }

    host_config_str = json.dumps(host_config, indent=2, ensure_ascii=False)
    print(host_config_str)
    put_str(c, '/data/ofm/config/http_host.json', host_config_str)


def prepare_http_host(c):
    nginx(c)
    certbot(c)

    c.sudo('rm -rf /data/ofm/http_host/logs')
    c.sudo('mkdir -p /data/ofm/http_host/logs')
    c.sudo('chown ofm:ofm /data/ofm/http_host/logs')

    c.sudo('rm -rf /data/ofm/http_host/logs_nginx')
    c.sudo('mkdir -p /data/ofm/http_host/logs_nginx')
    c.sudo('chown nginx:nginx /data/ofm/http_host/logs_nginx')

    upload_https_host_files(c)
    upload_certificates(c)

    c.sudo('/data/ofm/venv/bin/pip install -e /data/ofm/http_host/bin')


def add_http_host_cron(c):
    put(c, SCRIPTS_DIR / 'http_host' / 'cron.d' / 'ofm_http_host', '/etc/cron.d/')


def run_http_host_sync(c):
    sudo_cmd(c, '/data/ofm/venv/bin/python -u /data/ofm/http_host/bin/host_manager.py sync')


def upload_https_host_files(c):
    c.sudo(f'mkdir -p {HTTP_HOST_BIN}')

    put_dir(c, SCRIPTS_DIR / 'http_host', HTTP_HOST_BIN, file_permissions='755')
    put_dir(c, SCRIPTS_DIR / 'http_host' / 'http_host_lib', f'{HTTP_HOST_BIN}/http_host_lib')
    put_dir(
        c,
        SCRIPTS_DIR / 'http_host' / 'http_host_lib' / 'nginx',
        f'{HTTP_HOST_BIN}/http_host_lib/nginx',
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


def setup_le_dns_manager(c):
    le_email = dotenv_val('LE_EMAIL').lower()
    domain_le_dns = dotenv_val('DOMAIN_LE_DNS').lower()
    assert le_email
    assert domain_le_dns

    c.sudo('mkdir -p /root/.secrets')

    put(
        c,
        CONFIG_DIR / 'cloudflare.ini',
        '/root/.secrets/ofm_le_dns_cloudflare.ini',
        permissions=400,
    )

    sudo_cmd(
        c,
        'certbot certonly '
        '--dns-cloudflare '
        '--dns-cloudflare-credentials /root/.secrets/ofm_le_dns_cloudflare.ini '
        '--staging '
        f'--noninteractive -m {le_email} '
        f'--agree-tos '
        f'--cert-name=ofm_le_dns '
        f'-d {domain_le_dns}',
    )
