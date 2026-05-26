from shared_lib.ssh_lib.utils import put
from tilegen.deploy_lib.planetiler import install_planetiler
from tilegen.deploy_lib.tilegen_deploy_config import tilegen_deploy_config


def prepare_tilegen(c, *, enable_cron):
    c.sudo('rm -f /etc/cron.d/ofm_tilegen')
    install_planetiler(c)

    rclone_config = tilegen_deploy_config.local_config_dir / 'tilegen' / 'rclone.conf'
    if rclone_config.exists():
        put(
            c,
            rclone_config,
            f'{tilegen_deploy_config.remote_tilegen_config}/rclone.conf',
            permissions='600',
            user='ofm',
            create_parent_dir=True,
        )

    c.sudo('mkdir -p /data/ofm/tilegen/logs')
    c.sudo('chown ofm:ofm /data/ofm/tilegen /data/ofm/tilegen/logs')

    if enable_cron:
        install_tilegen_cron(c)


def install_tilegen_cron(c):
    put(c, tilegen_deploy_config.local_tilegen_dir / 'cron.d' / 'ofm_tilegen', '/etc/cron.d/')
