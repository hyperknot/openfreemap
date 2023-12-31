from ssh_lib import TILE_GEN_BIN
from ssh_lib.utils import apt_get_install, apt_get_update


PLANETILER_VERSION = '0.7.0'
PLANETILER_PATH = f'{TILE_GEN_BIN}/planetiler.jar'


def planetiler(c):
    apt_get_update(c)
    apt_get_install(c, 'openjdk-21-jre-headless')

    c.sudo(f'mkdir -p {TILE_GEN_BIN}')

    c.sudo(
        f'wget -q https://github.com/onthegomap/planetiler/releases/download/v{PLANETILER_VERSION}/planetiler.jar '
        f'-O {PLANETILER_PATH}',
    )

    c.sudo(f'java -jar {PLANETILER_PATH} --help', hide=True)
