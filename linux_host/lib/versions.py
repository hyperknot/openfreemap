from lib.get_version_shared import get_deployed_version
from linux_host.lib.config import config
from linux_host.lib.telegram_wrapper import telegram_send_message
from linux_host.lib.utils import assert_linux, assert_sudo


def get_remote_deployed_versions() -> dict[str, str]:
    print('Fetching remote deployed version files')

    remote_versions = {}
    for area in config.areas:
        deployed_version = get_deployed_version(area)['version']
        if not deployed_version:
            print(f'  deployed version not found: {area}')
            continue

        print(f'  remote deployed version {area}: {deployed_version}')
        remote_versions[area] = deployed_version

    return remote_versions


def fetch_version_files() -> bool:
    """
    Syncs remote deployed version files to local state, but only for versions
    that are already downloaded locally.
    """

    print('Syncing local version files')

    assert_linux()
    assert_sudo()

    return write_version_files(get_remote_deployed_versions())


def write_version_files(remote_versions: dict[str, str]) -> bool:
    need_nginx_sync = False

    for area, deployed_version in remote_versions.items():
        if not (config.runs_dir / area / deployed_version / 'tiles.btrfs').is_file():
            message = f'not switching {area} to {deployed_version}: local btrfs is missing'
            telegram_send_message(f'ERROR\n{message}')
            continue

        local_version_file = config.deployed_versions_dir / f'{area}.txt'

        try:
            local_version_old = local_version_file.read_text()
        except Exception:
            local_version_old = None

        if deployed_version != local_version_old:
            config.deployed_versions_dir.mkdir(exist_ok=True, parents=True)
            local_version_file.write_text(deployed_version)
            need_nginx_sync = True

    return need_nginx_sync
