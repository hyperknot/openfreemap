#!/usr/bin/env python3

from fabric import Connection

from openfreemaps.nginx import certbot, nginx
from openfreemaps.pkg_base import pkg_base, pkg_clean, pkg_upgrade
from openfreemaps.planetiler import install_planetiler
from openfreemaps.system import set_cpu_governor, setup_kernel_settings, setup_time


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


c = Connection(host='map128', port=22)

prepare_server(c)
# reboot(c)
