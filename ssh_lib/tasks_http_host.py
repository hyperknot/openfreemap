import json

from ssh_lib.benchmark import c1000k, wrk
from ssh_lib.config import config
from ssh_lib.kernel import kernel_limits1m, kernel_somaxconn65k
from ssh_lib.nginx import certbot, nginx
from ssh_lib.utils import put, put_dir, sudo_cmd


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
    if not config.local_config_jsonc.is_file():
        print(f'{config.local_config_jsonc} not found. Make sure it exists in the /config dir')
        return

    # validate using json5 + jsonschema
    config_data = json.loads(config.local_config_jsonc.read_text())

    # if ok, upload the file
    put(
        c,
        config.local_config_jsonc,
        f'{config.remote_config}/config.jsonc',
    )


def upload_http_host_files(c):
    c.sudo(f'rm -rf {config.http_host_bin}')
    c.sudo(f'mkdir -p {config.http_host_bin}')

    put_dir(c, config.local_modules_dir / 'http_host', config.http_host_bin, file_permissions='755')

    for dirname in ['http_host_lib', 'scripts']:
        put_dir(c, config.local_modules_dir / 'http_host' / dirname, f'{config.http_host_bin}/{dirname}')

    put_dir(
        c,
        config.local_modules_dir / 'http_host' / 'http_host_lib' / 'nginx_confs',
        f'{config.http_host_bin}/http_host_lib/nginx_confs',
    )

    c.sudo('chown -R ofm:ofm /data/ofm/http_host')


def run_http_host_sync(c):
    print('Running http_host.py sync --force')
    sudo_cmd(c, f'{config.venv_bin}/python -u {config.http_host_bin}/http_host.py sync --force')


def install_benchmark(c):
    """
    Read docs/quick_notes/http_benchmark.md
    """
    c1000k(c)
    wrk(c)
