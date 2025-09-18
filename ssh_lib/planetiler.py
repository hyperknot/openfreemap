from ssh_lib import PLANETILER_BIN, PLANETILER_SRC
from ssh_lib.java import java
from ssh_lib.utils import apt_get_install, apt_get_update, exists, sudo_cmd


# PLANETILER_COMMIT = '33b22c516e21cfbce6168ecba1c74486dc95d589'  # last good
PLANETILER_COMMIT = 'cc769c4f3c8d0ada8be7e650d3afdb4e92cbd3f2'  # main, not working

PLANETILER_PATH = f'{PLANETILER_BIN}/planetiler.jar'


def install_planetiler(c):
    if exists(c, PLANETILER_PATH):
        print('planetiler exists, skipping')
        return

    java(c)

    c.sudo('rm -rf /root/.m2')  # cleaning maven cache
    c.sudo(f'rm -rf {PLANETILER_BIN} {PLANETILER_SRC}')
    c.sudo(f'mkdir -p {PLANETILER_BIN} {PLANETILER_SRC}')

    c.sudo('git config --global advice.detachedHead false')
    c.sudo(
        f'git clone --recurse-submodules https://github.com/onthegomap/planetiler.git {PLANETILER_SRC}'
    )

    sudo_cmd(c, f'cd {PLANETILER_SRC} && git checkout {PLANETILER_COMMIT}')
    sudo_cmd(c, f'cd {PLANETILER_SRC} && git submodule update --init --recursive')

    sudo_cmd(c, f'cd {PLANETILER_SRC} && ./mvnw clean test package')

    c.sudo(
        f'mv {PLANETILER_SRC}/planetiler-dist/target/planetiler-dist-*-SNAPSHOT-with-deps.jar {PLANETILER_PATH}',
        warn=True,
    )

    c.sudo(f'java -jar {PLANETILER_PATH} --help', hide=True)

    c.sudo(f'rm -rf {PLANETILER_SRC}')
