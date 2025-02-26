from ssh_lib import PLANETILER_BIN, PLANETILER_SRC
from ssh_lib.utils import apt_get_install, apt_get_update, exists, sudo_cmd


PLANETILER_COMMIT = 'ee22a014022f1dcc120cba6a768567408ba74908'
PLANETILER_PATH = f'{PLANETILER_BIN}/planetiler.jar'


def install_planetiler(c):
    if exists(c, PLANETILER_PATH):
        print('planetiler exists, skipping')
        return

    apt_get_update(c)
    apt_get_install(c, 'openjdk-21-jre-headless')

    c.sudo(f'rm -rf {PLANETILER_BIN} {PLANETILER_SRC}')
    c.sudo(f'mkdir -p {PLANETILER_BIN} {PLANETILER_SRC}')

    c.sudo(
        f'git clone --recurse-submodules https://github.com/onthegomap/planetiler.git {PLANETILER_SRC}'
    )

    sudo_cmd(c, f'cd {PLANETILER_SRC} && git checkout {PLANETILER_COMMIT}')
    sudo_cmd(c, f'cd {PLANETILER_SRC} && git submodule update --init --recursive')

    sudo_cmd(c, f'cd {PLANETILER_SRC} && ./mvnw clean test package > {PLANETILER_SRC}/_build.log')

    c.sudo(
        f'mv {PLANETILER_SRC}/planetiler-dist/target/planetiler-dist-*-SNAPSHOT-with-deps.jar {PLANETILER_PATH}',
        warn=True,
    )

    c.sudo(f'java -jar {PLANETILER_PATH} --help', hide=True)

    c.sudo(f'rm -rf {PLANETILER_SRC}')
