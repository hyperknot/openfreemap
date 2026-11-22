import subprocess
import tempfile
from pathlib import Path

import requests
from fabric import Connection

from shared_lib.ssh_lib.java import update_java
from shared_lib.ssh_lib.utils import exists, sudo_cmd
from tilegen.deploy_tilegen.tilegen_deploy_config import tilegen_deploy_config


# Includes downloader HEAD retries (https://github.com/onthegomap/planetiler/pull/1621),
# the JTS snapshot fix for missing island holes (https://github.com/onthegomap/planetiler/issues/1622),
# --building-hide-outlines-with-parts (https://github.com/onthegomap/planetiler/pull/1643),
# Parquet water polygons from planetiler.onthegomap.com (https://github.com/onthegomap/planetiler/pull/1673)
# and the Geofabrik index fix (https://github.com/onthegomap/planetiler/pull/1701).
# After changing it, run ./tilegen/upload_planetiler.py before deploying.
PLANETILER_COMMIT = 'bf79fa5b2717c5a02575801efb9e98960c6a16ae'
PLANETILER_PATH = f'{tilegen_deploy_config.remote_planetiler_bin}/planetiler.jar'

PLANETILER_NAME = f'planetiler-{PLANETILER_COMMIT}'
PLANETILER_URL = f'https://assets.openfreemap.com/planetiler/{PLANETILER_NAME}.jar'


def install_planetiler(c: Connection) -> None:
    # Normal deploys preserve Java and Planetiler. Pin changes take effect only
    # after --reinstall removes /data/ofm and makes this path absent.
    if exists(c, PLANETILER_PATH):
        print('planetiler exists, skipping')
        return

    update_java(c)

    c.sudo(f'rm -rf {tilegen_deploy_config.remote_planetiler_bin}')
    c.sudo(f'mkdir -p {tilegen_deploy_config.remote_planetiler_bin}')
    sudo_cmd(c, f'curl -fsSL {PLANETILER_URL} -o {PLANETILER_PATH}')

    c.sudo(f'java -jar {PLANETILER_PATH} --help', hide=True)


def upload_planetiler_jar() -> None:
    """
    Copy the jar built and tested by Planetiler's snapshot CI for PLANETILER_COMMIT to the
    assets bucket, together with Planetiler's LICENSE and NOTICE.md (third-party licenses
    of the bundled libraries, like JTS). Needs an authenticated gh. CI artifacts expire
    after 90 days.
    Uses config/tilegen/rclone_local.conf, a local-only rclone config (same format as
    rclone.conf.sample) with write access to the assets bucket. Never deployed.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        run_id = subprocess.run(
            [
                'gh', 'run', 'list',
                '--repo', 'onthegomap/planetiler',
                '--workflow', 'snapshot.yml',
                '--commit', PLANETILER_COMMIT,
                '--status', 'success',
                '--limit', '1',
                '--json', 'databaseId',
                '--jq', '.[0].databaseId',
            ],
            check=True, capture_output=True, text=True,
        ).stdout.strip()  # fmt: skip
        if not run_id:
            raise RuntimeError(f'no successful Planetiler snapshot CI run for {PLANETILER_COMMIT}')

        subprocess.run(
            [
                'gh', 'run', 'download', run_id,
                '--repo', 'onthegomap/planetiler',
                '--name', 'planetiler-build',
                '--dir', tmp_dir,
            ],
            check=True,
        )  # fmt: skip
        jar = next(tmp_path.glob('planetiler-dist-*-with-deps.jar'))
        jar.rename(tmp_path / f'{PLANETILER_NAME}.jar')

        for name in ['LICENSE', 'NOTICE.md']:
            r = requests.get(
                f'https://raw.githubusercontent.com/onthegomap/planetiler/{PLANETILER_COMMIT}/{name}',
                timeout=30,
            )
            r.raise_for_status()
            (tmp_path / f'{PLANETILER_NAME}.{name}').write_bytes(r.content)

        subprocess.run(
            [
                'rclone', 'copy', '--checksum', '-vP',
                '--config', tilegen_deploy_config.local_tilegen_config_dir / 'rclone_local.conf',
                tmp_path, 'remote:ofm-assets/planetiler',
            ],
            check=True,
        )  # fmt: skip

    print(f'uploaded {PLANETILER_URL}')
