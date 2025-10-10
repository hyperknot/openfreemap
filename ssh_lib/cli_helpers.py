import os

import click
from fabric import Config, Connection


def get_connection(hostname, user, port):
    ssh_passwd = os.getenv('SSH_PASSWD')

    if ssh_passwd:
        print('Using SSH password')

        c = Connection(
            host=hostname,
            user=user,
            port=port,
            connect_kwargs={'password': ssh_passwd},
            config=Config(overrides={'sudo': {'password': ssh_passwd}}),
        )
    else:
        c = Connection(
            host=hostname,
            user=user,
            port=port,
        )

    return c


def common_options(func):
    """Decorator to define common options."""
    func = click.argument('hostname')(func)
    func = click.option('--port', type=int, help='SSH port (if not in .ssh/config)')(func)
    func = click.option('--user', help='SSH user (if not in .ssh/config)')(func)
    func = click.option('-y', '--noninteractive', is_flag=True, help='Skip confirmation questions')(
        func
    )
    return func
