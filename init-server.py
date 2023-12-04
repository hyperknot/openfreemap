#!/usr/bin/env python3

from fabric import Connection

from lib.nginx import certbot, nginx
from lib.pkg_base import pkg_base, pkg_clean, pkg_upgrade
from lib.planetiler import install_planetiler
from lib.system1 import set_cpu_governor, setup_kernel_settings, setup_time
from lib.utils import add_user


def prepare_server(c):
    add_user(c, 'ofm')

    # pkg_upgrade(c)
    # pkg_clean(c)
    # pkg_base(c)

    # setup_time(c)
    # setup_kernel_settings(c)
    # set_cpu_governor(c)

    # nginx(c)
    # certbot(c)

    install_planetiler(c)


c = Connection(host='ofm-o-ca-1', port=22, user='ubuntu')

prepare_server(c)
# reboot(c)
