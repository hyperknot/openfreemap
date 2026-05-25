from .config import config
from .pkg_base import pkg_base, pkg_upgrade
from .rclone import rclone
from .utils import add_user, enable_sudo, put, sudo_cmd


def prepare_shared(c):
    # creates ofm user with uid=2000, disabled password and nopasswd sudo
    add_user(c, 'ofm', uid=2000, system=False)
    enable_sudo(c, 'ofm', nopasswd=True)

    pkg_upgrade(c)
    pkg_base(c)
    rclone(c)

    c.sudo(f'mkdir -p {config.remote_config}')
    c.sudo(f'chown ofm:ofm {config.remote_config}')
    c.sudo(f'chown ofm:ofm {config.ofm_dir}')

    prepare_venv(c)


def prepare_venv(c):
    put(
        c,
        config.local_modules_dir / 'prepare-virtualenv.sh',
        config.ofm_dir,
        permissions='755',
        user='ofm',
    )
    sudo_cmd(c, f'cd {config.ofm_dir} && source prepare-virtualenv.sh')
