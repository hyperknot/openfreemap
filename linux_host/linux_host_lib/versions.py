from linux_host.linux_host_lib.linux_host_config import get_linux_host_config
from shared_lib.utils.get_version import get_deployed_version


def get_remote_deployed_versions() -> dict[str, str]:
    print('Fetching remote deployed version files')

    remote_versions: dict[str, str] = {}
    for area in get_linux_host_config().areas:
        remote_versions[area] = get_deployed_version(area)
        print(f'  remote deployed version {area}: {remote_versions[area]}')

    return remote_versions


def write_version_files(remote_versions: dict[str, str]) -> None:
    for area, deployed_version in remote_versions.items():
        local_version_file = get_linux_host_config().deployed_versions_dir / f'{area}.txt'
        try:
            local_version_old = local_version_file.read_text().strip()
        except OSError:
            local_version_old = None

        if deployed_version != local_version_old:
            get_linux_host_config().deployed_versions_dir.mkdir(exist_ok=True, parents=True)
            local_version_file.write_text(deployed_version)
            print(f'  switched {area} {local_version_old} → {deployed_version}')
