from fabric import Connection

from shared_lib.ssh_lib.utils import put
from tilegen.deploy_tilegen.install_planetiler import install_planetiler
from tilegen.deploy_tilegen.install_pmtiles import install_pmtiles
from tilegen.deploy_tilegen.tilegen_deploy_config import tilegen_deploy_config


def prepare_tilegen(c: Connection, *, enable_cron: bool) -> None:
    c.sudo('rm -f /etc/cron.d/ofm_tilegen')

    install_planetiler(c)
    install_pmtiles(c)

    rclone_config = tilegen_deploy_config.local_tilegen_config_dir / 'rclone.conf'
    if rclone_config.exists():
        put(
            c,
            rclone_config,
            f'{tilegen_deploy_config.remote_tilegen_config}/rclone.conf',
            permissions='600',
            user='ofm',
            create_parent_dir=True,
        )

    c.sudo(f'mkdir -p {tilegen_deploy_config.remote_tilegen_dir}/logs')
    c.sudo(
        f'chown ofm:ofm {tilegen_deploy_config.remote_tilegen_dir} '
        + f'{tilegen_deploy_config.remote_tilegen_dir}/logs'
    )

    if enable_cron:
        put(c, tilegen_deploy_config.local_tilegen_dir / 'cron.d' / 'ofm_tilegen', '/etc/cron.d/')
