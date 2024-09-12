import subprocess

from tile_gen_lib.config import config
from tile_gen_lib.shared import check_host_version, get_versions_for_area


def check_and_set_version(area, version):
    if version == 'latest':
        versions = get_versions_for_area(area)
        if not versions:
            print(f'  No versions found for {area}')
            return

        version = versions[-1]
        print(f'  Latest version on bucket: {area} {version}')

    if not check_all_hosts(area, version):
        return

    set_version(area, version)


def set_version(area, version):
    print(f'setting version: {area} {version}')
    subprocess.run(
        [
            config.rclone_bin,
            'rcat',
            f'remote:ofm-assets/deployed_versions/{area}.txt',
        ],
        env=dict(RCLONE_CONFIG=config.rclone_config),
        check=True,
        input=version.strip().encode(),
    )


def check_all_hosts(area, version) -> bool:
    oc = config.ofm_config

    domain = oc['domain_ledns'] or oc['domain_le']
    print(f'Using domain: {domain}')

    try:
        for host_ip in oc['http_host_list']:
            print(f'Checking {area} {version} on host {host_ip}')
            check_host_version(domain, host_ip, area, version)
        return True
    except Exception:
        print('Error, version not available')
        return False
