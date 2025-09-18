from ssh_lib.utils import (
    apt_get_install,
    apt_get_update,
)


def pkg_base(c):
    pkg_list = [
        'aria2',
        'build-essential',
        'curl',
        'dnsutils',
        'git',
        'htop',
        'lsb-release',
        'pigz',
        'rsync',
        'unzip',
        'wget',
        'psmisc',
        'util-linux',
        #
        'btrfs-progs',
        #
        'ca-certificates',
        'gnupg-agent',
        'gnupg2',
        'ubuntu-keyring',
        #
        'iftop',
        'nload',
        'vnstat',
        #
        'python3',
        'python3-venv',
        #
        'acpid',
        'autojump',
        'bash-completion',
        'btop',
        'ctop',
        'dbus',
        'direnv',
        'fd-find',
        'file',
        'ioping',
        'libffi-dev',
        'libssl-dev',
        'lsof',
        'man-db',
        'mc',
        'nano',
        'ncdu',
        'net-tools',
        'netbase',
        'nethogs',
        'openssh-client',
        'p7zip-full',
        'pkg-config',
        'psmisc',
        'ripgrep',
        'silversearcher-ag',
        'time',
        'tmux',
        #
        # 'dstat',
        # 'iperf3',
        # 'iproute2',
        # 'nasm',
    ]

    apt_get_install(c, ' '.join(pkg_list))

    c.sudo('ln -snf $(which fdfind) /usr/local/bin/fd', warn=True)


def pkg_upgrade(c):
    apt_get_update(c)
    c.sudo(
        'DEBIAN_FRONTEND=noninteractive apt-get dist-upgrade -y -o Dpkg::Options::="--force-confold"'
    )
