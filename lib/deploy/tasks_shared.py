from lib.ssh_lib.pkg_base import pkg_base, pkg_upgrade
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

    upload_source(c, deploy_config)
    prepare_uv(c, deploy_config)


def upload_source(c, deploy_config):
    put_dir_tarball(
        c,
        deploy_config.repo_root,
        deploy_config.source_dir,
        user='ofm',
        exclude_set={
            '*.egg-info',
            '*.pyc',
            '.DS_Store',
            '.astro',
            '.git',
            '.ipynb_checkpoints',
            '.mypy_cache',
            '.pnpm-store',
            '.pytest_cache',
            '.ruff_cache',
            '.venv',
            '.wrangler',
            '__pycache__',
            'dist',
            'node_modules',
            'venv',
        },
    )


def prepare_uv(c, deploy_config):
    sudo_cmd(
        c, 'command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh', user='ofm'
    )
    c.sudo('test ! -x /home/ofm/.local/bin/uv || ln -sf /home/ofm/.local/bin/uv /usr/local/bin/uv')
    sudo_cmd(c, 'uv sync', user='ofm', cwd=deploy_config.source_dir)
