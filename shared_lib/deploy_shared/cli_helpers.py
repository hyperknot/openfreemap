import os
from collections.abc import Callable
from typing import Any

import click
from fabric import Config, Connection
from invoke.exceptions import UnexpectedExit


def get_connection(hostname: str, user: str | None, port: int | None) -> Connection:
    ssh_password = os.getenv('SSH_PASSWD')
    sudo_password = os.getenv('SUDO_PASSWD', ssh_password)

    connect_kwargs: dict[str, Any] = {}
    if ssh_password:
        print('Using SSH password')
        connect_kwargs = {
            'password': ssh_password,
            'allow_agent': False,
            'look_for_keys': False,
        }

    config = None
    if sudo_password:
        config = Config(overrides={'sudo': {'password': sudo_password}, 'run': {'pty': True}})

    c = Connection(
        host=hostname,
        user=user,
        port=port,
        connect_kwargs=connect_kwargs,
        config=config,
    )
    check_sudo(c, sudo_password=bool(sudo_password))
    return c


def check_sudo(c: Connection, *, sudo_password: bool) -> None:
    if c.run('id -u', hide=True).stdout.strip() == '0':
        if c.run('command -v sudo', hide=True, warn=True).ok:
            return
        raise click.ClickException(
            'Root SSH user is missing sudo. Install sudo on the server first.'
        )

    if sudo_password:
        try:
            c.sudo('true', hide=True)
        except UnexpectedExit as e:
            raise click.ClickException(
                'SSH user could not run sudo with the provided password. Check that the user is '
                + 'in the sudo group and that SUDO_PASSWD/SSH_PASSWD is correct.'
            ) from e
        return

    if c.run('sudo -n true', hide=True, warn=True).ok:
        return

    raise click.ClickException(
        'SSH user cannot run passwordless sudo. Use a root SSH user, configure NOPASSWD sudo, '
        + 'or set SUDO_PASSWD/SSH_PASSWD for password-based sudo.'
    )


def common_options(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to define common options."""
    decorated = click.argument('hostname')(func)
    decorated = click.option('--port', type=int, help='SSH port (if not in .ssh/config)')(decorated)
    decorated = click.option('--user', help='SSH user (if not in .ssh/config)')(decorated)
    decorated = click.option(
        '-y', '--noninteractive', is_flag=True, help='Skip confirmation questions'
    )(decorated)
    return decorated
