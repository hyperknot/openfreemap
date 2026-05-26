from .apt import (
    apt_get_install,
    apt_get_purge,
    apt_get_update,
    setup_apt_repository,
)
from .utils import (
    ubuntu_codename,
)


JAVA_VER = 24
ADOPTIUM_REPO_NAME = 'adoptium'


def java(c):
    """Install OpenJDK from Eclipse Adoptium."""
    # remove old Ubuntu version of OpenJDK
    apt_get_purge(c, 'openjdk* temurin*')

    codename = ubuntu_codename(c)

    setup_apt_repository(
        c,
        repo_name=ADOPTIUM_REPO_NAME,
        key_url='https://packages.adoptium.net/artifactory/api/gpg/key/public',
        repo_url='https://packages.adoptium.net/artifactory/deb',
        suite=codename,
        component='main',
    )

    apt_get_update(c)
    apt_get_install(c, f'temurin-{JAVA_VER}-jdk')

    # Verify installation
    c.run('java -version')
