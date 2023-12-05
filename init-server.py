#!/usr/bin/env python3
import sys

from dotenv import dotenv_values
from fabric import Config, Connection

from ssh_lib.kernel import set_cpu_governor, setup_kernel_settings
from ssh_lib.nginx import certbot, nginx
from ssh_lib.pkg_base import pkg_base, pkg_clean, pkg_upgrade
from ssh_lib.planetiler import install_planetiler
from ssh_lib.utils import reboot, setup_time


def prepare_server(c):
    pkg_upgrade(c)
    pkg_clean(c)
    pkg_base(c)

    setup_time(c)
    setup_kernel_settings(c)
    set_cpu_governor(c)

    nginx(c)
    certbot(c)

    install_planetiler(c)


HOSTNAME = sys.argv[1]

OFM_USER_PASSWD = dotenv_values('.env')['OFM_USER_PASSWD']
assert OFM_USER_PASSWD

if input(f'run {sys.argv[0]} on {HOSTNAME}? [y/N]: ') != 'y':
    sys.exit()


c = Connection(
    host=HOSTNAME,
    config=Config(overrides={'sudo': {'password': OFM_USER_PASSWD}}),
)
prepare_server(c)
reboot(c)
