from lib.ssh_lib.pkg_base import pkg_base, pkg_upgrade
from lib.ssh_lib.python_uv import python_uv
from lib.ssh_lib.rclone import rclone
from lib.ssh_lib.utils import add_user, enable_sudo, put_dir_tarball, sudo_cmd


def prepare_shared(c, deploy_config):
    # Creates ofm user with uid=2000, disabled password and nopasswd sudo.
    add_user(c, 'ofm', uid=2000, system=False)
    enable_sudo(c, 'ofm', nopasswd=True)

    pkg_upgrade(c)
    pkg_base(c)
    rclone(c)

    c.sudo(f'mkdir -p {deploy_config.remote_config}')
    c.sudo(f'chown ofm:ofm {deploy_config.remote_config}')
    c.sudo(f'chown ofm:ofm {deploy_config.ofm_dir}')

    python_uv(c)

    put_dir_tarball(
        c,
        deploy_config.repo_root,
        deploy_config.source_dir,
        user='ofm',
        exclude_set={
            '.astro',
            '.git',
            '.ruff_cache',
            '.venv',
            '.wrangler',
            '__pycache__',
            'dist',
            'node_modules',
        },
    )

    sudo_cmd(c, 'uv sync', user='ofm', cwd=deploy_config.source_dir)
