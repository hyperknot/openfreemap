from .config import config
from .pkg_base import pkg_base, pkg_upgrade
from .rclone import rclone
from .utils import add_user, enable_sudo, put_source_dir, sudo_cmd


def prepare_shared(c):
    # Creates ofm user with uid=2000, disabled password and nopasswd sudo.
    add_user(c, 'ofm', uid=2000, system=False)
    enable_sudo(c, 'ofm', nopasswd=True)

    pkg_upgrade(c)
    pkg_base(c)
    rclone(c)

    c.sudo(f'mkdir -p {config.remote_config}')
    c.sudo(f'chown ofm:ofm {config.remote_config}')
    c.sudo(f'chown ofm:ofm {config.ofm_dir}')

    upload_source(c)
    prepare_uv(c)


def upload_source(c):
    put_source_dir(c, config.repo_root, config.source_dir, user='ofm')


def prepare_uv(c):
    sudo_cmd(
        c, 'command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh', user='ofm'
    )
    c.sudo('test ! -x /home/ofm/.local/bin/uv || ln -sf /home/ofm/.local/bin/uv /usr/local/bin/uv')
    sudo_cmd(c, 'uv sync --python=3.12 --no-dev', user='ofm', cwd=config.source_dir)
