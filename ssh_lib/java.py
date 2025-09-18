from ssh_lib.utils import (
    apt_get_install,
    apt_get_purge,
    apt_get_update,
    put_str,
    sudo_cmd,
    ubuntu_codename,
)


JAVA_VER = 24


def java(c):
    """Install OpenJDK from Eclipse Adoptium."""
    # remove old Ubuntu version of OpenJDK
    apt_get_purge(c, 'openjdk* temurin*')

    # Download and install the Eclipse Adoptium GPG key
    sudo_cmd(
        c,
        'wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public '
        '| gpg --dearmor '
        '| tee /etc/apt/trusted.gpg.d/adoptium.gpg > /dev/null',
    )

    # Get the Ubuntu codename
    codename = ubuntu_codename(c)

    # Configure the Eclipse Adoptium apt repository
    put_str(
        c,
        '/etc/apt/sources.list.d/adoptium.list',
        f'deb https://packages.adoptium.net/artifactory/deb {codename} main',
    )

    # Update package list and install Temurin JDK
    apt_get_update(c)
    apt_get_install(c, f'temurin-{JAVA_VER}-jdk')

    # Verify installation
    c.run('java -version')
