from ssh_lib.utils import apt_get_install, apt_get_update


PLANETILER_VERSION = '0.7.0'

TILE_GEN_BIN = '/data/ofm/tile_gen'
PLANETILER_PATH = f'{TILE_GEN_BIN}/planetiler.jar'


def install_planetiler(c):
    apt_get_update(c)
    apt_get_install(c, 'openjdk-17-jdk')

    c.sudo(f'mkdir -p {TILE_GEN_BIN}')

    c.sudo(
        f'wget -q https://github.com/onthegomap/planetiler/releases/download/v{PLANETILER_VERSION}/planetiler.jar '
        f'-O {PLANETILER_PATH}',
    )

    c.sudo(f'java -jar {PLANETILER_PATH} --help', hide=True)

    c.sudo('chown -R ofm:ofm /data/ofm')
