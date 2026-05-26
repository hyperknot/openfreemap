from shared_lib.ssh_lib.pkg_base import pkg_base, pkg_upgrade
from shared_lib.ssh_lib.python_uv import python_uv
from shared_lib.ssh_lib.rclone import rclone
from shared_lib.ssh_lib.utils import add_user, enable_sudo, put_dir_tarball, sudo_cmd


def prepare_shared(c, deploy_config):
    # Creates ofm user with uid=2000, disabled password and nopasswd sudo.
    add_user(c, 'ofm', uid=2000, system=False)
    enable_sudo(c, 'ofm', nopasswd=True)

    pkg_upgrade(c)
    pkg_base(c)
    rclone(c)

    c.sudo(f'mkdir -p {deploy_config.remote_config_dir}')
    c.sudo(f'chown ofm:ofm {deploy_config.remote_config_dir}')
    c.sudo(f'chown ofm:ofm {deploy_config.remote_ofm_dir}')

    python_uv(c)

    put_dir_tarball(
        c,
        deploy_config.local_repo_root,
        deploy_config.remote_source_dir,
        user='ofm',
        exclude_patterns={
            '.astro',
            '.ruff_cache',
            '.venv',
            '.wrangler',
            '__pycache__',
            'cron.d',
            'dist',
            'node_modules',
            #
            '/.git',
            '/.github',
            '/config',
            '/docs',
            '/linux_host/deploy_linux_host',
            '/shared_lib/assets',
            '/shared_lib/deploy_shared',
            '/shared_lib/ssh_lib',
            '/tilegen/deploy_tilegen',
            '/website',
        },
    )

    sudo_cmd(c, 'uv sync', user='ofm', cwd=deploy_config.remote_source_dir)
