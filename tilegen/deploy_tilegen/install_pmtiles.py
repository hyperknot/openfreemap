from fabric import Connection

from shared_lib.ssh_lib.utils import exists, get_arch, sudo_cmd
from tilegen.deploy_tilegen.tilegen_deploy_config import tilegen_deploy_config


GO_PMTILES_RELEASE = '1.30.2'
PMTILES_PATH = f'{tilegen_deploy_config.remote_pmtiles_bin}/pmtiles'


def install_pmtiles(c: Connection) -> None:
    if exists(c, PMTILES_PATH):
        print('pmtiles exists, skipping')
        return

    c.sudo(f'rm -rf {tilegen_deploy_config.remote_pmtiles_bin}')
    c.sudo(f'mkdir -p {tilegen_deploy_config.remote_pmtiles_bin}')

    arch = get_arch(c)
    if arch == 'x86_64':
        pmtiles_arch = 'x86_64'
    elif arch in {'aarch64', 'arm64'}:
        pmtiles_arch = 'arm64'
    else:
        raise ValueError(f'Unsupported architecture: {arch}')

    sudo_cmd(
        c,
        f'curl -fsSL https://github.com/protomaps/go-pmtiles/releases/download/v{GO_PMTILES_RELEASE}/go-pmtiles_{GO_PMTILES_RELEASE}_Linux_{pmtiles_arch}.tar.gz -o /tmp/go-pmtiles.tar.gz && '
        f'tar -xzf /tmp/go-pmtiles.tar.gz -C {tilegen_deploy_config.remote_pmtiles_bin} pmtiles && '
        f'chmod +x {PMTILES_PATH} && '
        'rm -f /tmp/go-pmtiles.tar.gz',
    )

    c.sudo(f'{PMTILES_PATH} --help', hide=True)
