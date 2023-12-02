from openfreemaps.config import templates
from openfreemaps.utils import apt_get_install, apt_get_update, put


PLANETILER_VERSION = '0.7.0'

PLANETILER_DIR = '/data/planetiler/bin'
PLANETILER_PATH = f'{PLANETILER_DIR}/planetiler.jar'


def install_planetiler(c):
    apt_get_update(c)
    apt_get_install(c, 'openjdk-17-jdk')

    c.run('mkdir -p /data/planetiler/bin')

    c.run(
        f'wget -q https://github.com/onthegomap/planetiler/releases/download/v{PLANETILER_VERSION}/planetiler.jar '
        f'-O {PLANETILER_PATH}',
    )

    c.run(f'java -jar {PLANETILER_PATH} --help')
    put(c, templates / 'planetiler' / 'run_planet.sh', PLANETILER_DIR, permissions='755')
