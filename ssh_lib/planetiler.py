from ssh_lib import TILE_GEN_BIN, TILE_GEN_SRC
from ssh_lib.utils import apt_get_install, apt_get_update, sudo_cmd


PLANETILER_COMMIT = 'cf6c55'
PLANETILER_PATH = f'{TILE_GEN_BIN}/planetiler.jar'


def planetiler(c):
    apt_get_update(c)
    apt_get_install(c, 'openjdk-21-jre-headless')

    c.sudo(f'rm -rf {TILE_GEN_BIN} {TILE_GEN_SRC}')
    c.sudo(f'mkdir -p {TILE_GEN_BIN} {TILE_GEN_SRC}')

    c.sudo(
        f'git clone --recurse-submodules https://github.com/onthegomap/planetiler.git {TILE_GEN_SRC}'
    )

    sudo_cmd(c, f'cd {TILE_GEN_SRC} && git checkout {PLANETILER_COMMIT}')
    sudo_cmd(c, f'cd {TILE_GEN_SRC} && git submodule update --init --recursive')

    sudo_cmd(c, f'cd {TILE_GEN_SRC} && ./mvnw clean test package > {TILE_GEN_SRC}/_build.log')

    c.sudo(
        f'mv {TILE_GEN_SRC}/planetiler-dist/target/planetiler-dist-*-SNAPSHOT-with-deps.jar {PLANETILER_PATH}',
        warn=True,
    )

    c.sudo(f'java -jar {PLANETILER_PATH} --help', hide=True)

    c.sudo(f'rm -rf {TILE_GEN_SRC}')
