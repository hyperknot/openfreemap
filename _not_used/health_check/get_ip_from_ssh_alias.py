import socket

from fabric import Connection


def get_ip_from_ssh_alias(ssh_alias: str) -> str:
    """
    Get IP address from SSH config alias.

    Args:
        ssh_alias: SSH hostname/alias from ~/.ssh/config

    Returns:
        str: IP address

    Raises:
        socket.gaierror: If hostname cannot be resolved
    """

    # Create connection (doesn't actually connect)
    conn = Connection(ssh_alias)

    hostname = f'{conn.host or ""}'
    if not hostname:
        raise RuntimeError(f'Could not resolve hostname for SSH alias {ssh_alias!r}')

    return socket.gethostbyname(hostname)
