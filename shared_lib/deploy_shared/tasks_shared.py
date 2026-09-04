import json
import subprocess
import tempfile
from datetime import UTC, datetime
from typing import Any

from fabric import Connection

from shared_lib.ssh_lib.devops import ensure_uv
from shared_lib.ssh_lib.pkg_base import pkg_base, pkg_upgrade
from shared_lib.ssh_lib.utils import add_user, enable_sudo, put, put_dir_tarball, sudo_cmd


def prepare_shared(c: Connection, deploy_config: Any) -> None:
    # Creates ofm user with uid=2000, disabled password and nopasswd sudo.
    add_user(c, 'ofm', uid=2000, system=False)
    enable_sudo(c, 'ofm', nopasswd=True)

    pkg_upgrade(c)
    pkg_base(c)
    ensure_uv(c)

    c.sudo(f'mkdir -p {deploy_config.remote_config_dir}')
    c.sudo(f'chown ofm:ofm {deploy_config.remote_config_dir}')
    c.sudo(f'chown ofm:ofm {deploy_config.remote_ofm_dir}')

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

    deployed_version = {
        'commit': subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=deploy_config.local_repo_root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip(),
        'branch': subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd=deploy_config.local_repo_root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip(),
        'deployed_at': datetime.now(UTC).isoformat(),
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as file:
        json.dump(deployed_version, file)
        file.flush()
        put(
            c,
            file.name,
            f'{deploy_config.remote_source_dir}/deployed_version.json',
            user='ofm',
        )

    sudo_cmd(c, 'uv sync', user='ofm', cwd=deploy_config.remote_source_dir)
