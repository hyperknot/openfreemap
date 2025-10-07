import json
import sys

from ssh_lib.benchmark import c1000k, wrk
from ssh_lib.config import config
from ssh_lib.kernel import kernel_limits1m, kernel_somaxconn65k
from ssh_lib.nginx import certbot, nginx
from ssh_lib.utils import put_dir, put_str, sudo_cmd


def prepare_http_host(c):
    kernel_somaxconn65k(c)
    kernel_limits1m(c)

    upload_config_json(c)

    nginx(c)
    certbot(c)

    c.sudo(f'rm -rf {config.http_host_dir}/logs')
    c.sudo(f'mkdir -p {config.http_host_dir}/logs')
    c.sudo(f'chown ofm:ofm {config.http_host_dir}/logs')

    c.sudo(f'rm -rf {config.http_host_dir}/logs_nginx')
    c.sudo(f'mkdir -p {config.http_host_dir}/logs_nginx')
    c.sudo(f'chown nginx:nginx {config.http_host_dir}/logs_nginx')

    upload_http_host_files(c)

    c.sudo(f'{config.venv_bin}/pip install -e {config.http_host_bin} --use-pep517')


def upload_config_json(c):
    config.config_jsonc.is_file()
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
