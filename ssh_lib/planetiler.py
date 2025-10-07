from ssh_lib.config import config
from ssh_lib.java import java
from ssh_lib.utils import exists, sudo_cmd


PLANETILER_COMMIT = 'cc769c'
PLANETILER_PATH = f'{config.planetiler_bin}/planetiler.jar'


def install_planetiler(c):
    if exists(c, PLANETILER_PATH):
        print('planetiler exists, skipping')
        return

    java(c)

    c.sudo('rm -rf /root/.m2')  # cleaning maven cache
    c.sudo(f'rm -rf {config.planetiler_bin} {config.planetiler_src}')
    c.sudo(f'mkdir -p {config.planetiler_bin} {config.planetiler_src}')

    c.sudo('git config --global advice.detachedHead false')
    c.sudo(
        f'git clone --recurse-submodules https://github.com/onthegomap/planetiler.git {config.planetiler_src}'
    )

    sudo_cmd(c, f'cd {config.planetiler_src} && git checkout {PLANETILER_COMMIT}')
    sudo_cmd(c, f'cd {config.planetiler_src} && git submodule update --init --recursive')

    sudo_cmd(c, f'cd {config.planetiler_src} && ./mvnw clean test package')

    c.sudo(
        f'mv {config.planetiler_src}/planetiler-dist/target/planetiler-dist-*-SNAPSHOT-with-deps.jar {PLANETILER_PATH}',
        warn=True,
    )

    c.sudo(f'java -jar {PLANETILER_PATH} --help', hide=True)

    c.sudo(f'rm -rf {config.planetiler_src}')
