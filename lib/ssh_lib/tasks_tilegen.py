from .config import config
from .planetiler import install_planetiler
from .utils import put


def prepare_tilegen(c, *, enable_cron):
    c.sudo('rm -f /etc/cron.d/ofm_tilegen')
    install_planetiler(c)

    if (config.local_config_dir / 'rclone.conf').exists():
        put(
            c,
            config.local_config_dir / 'rclone.conf',
            f'{config.remote_config}/rclone.conf',
            permissions='600',
            user='ofm',
        )

    c.sudo('mkdir -p /data/ofm/tilegen/logs')
    c.sudo('chown ofm:ofm /data/ofm/tilegen /data/ofm/tilegen/logs')

    if enable_cron:
        install_tilegen_cron(c)


def install_tilegen_cron(c):
    put(c, config.local_tilegen_dir / 'cron.d' / 'ofm_tilegen', '/etc/cron.d/')
