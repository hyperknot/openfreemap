from fabric import Connection

from shared_lib.ssh_lib.java import java
from shared_lib.ssh_lib.utils import exists, sudo_cmd
from tilegen.deploy_tilegen.tilegen_deploy_config import tilegen_deploy_config


PLANETILER_COMMIT = 'f91cc19d'
PLANETILER_PATH = f'{tilegen_deploy_config.remote_planetiler_bin}/planetiler.jar'


def install_planetiler(c: Connection) -> None:
    if exists(c, PLANETILER_PATH):
        print('planetiler exists, skipping')
        return

    java(c)

    c.sudo('rm -rf /root/.m2')  # cleaning maven cache
    c.sudo(
        f'rm -rf {tilegen_deploy_config.remote_planetiler_bin} {tilegen_deploy_config.remote_planetiler_src}'
    )
    c.sudo(
        f'mkdir -p {tilegen_deploy_config.remote_planetiler_bin} {tilegen_deploy_config.remote_planetiler_src}'
    )

    c.sudo('git config --global advice.detachedHead false')
    c.sudo(
        f'git clone --recurse-submodules https://github.com/onthegomap/planetiler.git {tilegen_deploy_config.remote_planetiler_src}'
    )

    sudo_cmd(
        c, f'cd {tilegen_deploy_config.remote_planetiler_src} && git checkout {PLANETILER_COMMIT}'
    )
    sudo_cmd(
        c,
        f'cd {tilegen_deploy_config.remote_planetiler_src} && git submodule update --init --recursive',
    )

    sudo_cmd(c, f'cd {tilegen_deploy_config.remote_planetiler_src} && ./mvnw clean test package')

    c.sudo(
        f'mv {tilegen_deploy_config.remote_planetiler_src}/planetiler-dist/target/planetiler-dist-*-SNAPSHOT-with-deps.jar {PLANETILER_PATH}',
        warn=True,
    )

    c.sudo(f'java -jar {PLANETILER_PATH} --help', hide=True)

    c.sudo(f'rm -rf {tilegen_deploy_config.remote_planetiler_src}')
