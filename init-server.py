#!/usr/bin/env python3

from fabric import Connection

from openfreemaps.kernel import setup_kernel_settings
from openfreemaps.nginx import certbot, nginx


def prepare_server(c):
    setup_kernel_settings(c)

    nginx(c)
    certbot(c)


c = Connection(host='map128')

prepare_server(c)
