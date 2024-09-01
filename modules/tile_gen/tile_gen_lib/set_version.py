import subprocess

from http_host_lib.config import config

from tile_gen_lib.shared import get_versions_for_area


def check_all_hosts(area, version):
    pass


def check_and_set_version(area, version):
    if version == 'latest':
        versions = get_versions_for_area(area)
        version = versions[-1]

    if not check_all_hosts(area, version):
        return


def set_version(area, version):
    subprocess.run(
        [
            'rclone',
            'rcat',
            f'remote:ofm-assets/deployed_versions/{area}.txt',
        ],
        env=dict(RCLONE_CONFIG=config.rclone_config),
        check=True,
        input=version.strip().encode(),
    )
