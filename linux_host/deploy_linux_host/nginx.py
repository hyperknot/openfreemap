from fabric import Connection

from linux_host.deploy_linux_host.linux_host_deploy_config import linux_host_deploy_config
from shared_lib.ssh_lib.config import config
from shared_lib.ssh_lib.nginx import deploy_nginx_base_config
from shared_lib.ssh_lib.utils import put


LOGROTATE_PATH = '/etc/logrotate.d/openfreemap-nginx'


def configure_nginx(c: Connection) -> None:
    deploy_nginx_base_config(c, config.local_assets_dir / 'nginx')
    put(
        c,
        linux_host_deploy_config.local_linux_host_dir / 'logrotate.d' / 'openfreemap-nginx',
        LOGROTATE_PATH,
        permissions='0644',
    )
    c.sudo(f'logrotate --debug {LOGROTATE_PATH}')
    c.sudo('systemctl enable --now logrotate.timer')
