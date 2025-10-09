from ssh_lib.config import config
from ssh_lib.planetiler import install_planetiler
from ssh_lib.utils import put, put_dir


def prepare_tile_gen(c, *, enable_cron):
    c.sudo('rm -f /etc/cron.d/ofm_tile_gen')

    install_planetiler(c)

    c.sudo(f'rm -rf {config.tile_gen_bin}')

    put_dir(c, config.local_modules_dir / 'tile_gen', config.tile_gen_bin, file_permissions='755')

    for dirname in ['tile_gen_lib', 'scripts']:
        put_dir(
            c, config.local_modules_dir / 'tile_gen' / dirname, f'{config.tile_gen_bin}/{dirname}'
        )

    if (config.local_config_dir / 'rclone.conf').exists():
        put(
            c,
            config.local_config_dir / 'rclone.conf',
            f'{config.remote_config}/rclone.conf',
            permissions='600',
            user='ofm',
        )

    c.sudo(f'{config.venv_bin}/pip install -e {config.tile_gen_bin} --use-pep517')

    c.sudo('rm -rf /data/ofm/tile_gen/logs')
    c.sudo('mkdir -p /data/ofm/tile_gen/logs')

    c.sudo('chown ofm:ofm /data/ofm/tile_gen/{,*}')
    c.sudo(f'chown ofm:ofm -R {config.tile_gen_bin}')

    if enable_cron:
        put(c, config.local_modules_dir / 'tile_gen' / 'cron.d' / 'ofm_tile_gen', '/etc/cron.d/')
