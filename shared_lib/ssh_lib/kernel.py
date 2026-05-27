from fabric import Connection

from .config import config
from .utils import put, put_str


def kernel_somaxconn65k(c: Connection) -> None:
    put_str(c, '/etc/sysctl.d/60-somaxconn65k.conf', 'net.core.somaxconn = 65535')


def kernel_limits1m(c: Connection) -> None:
    put_str(
        c,
        '/etc/security/limits.d/limits1m.conf',
        """
            * soft nofile 1048576
            * hard nofile 1048576
            root soft nofile 1048576
            root hard nofile 1048576
        """,
    )


def kernel_vmovercommit(c: Connection) -> None:
    put_str(c, '/etc/sysctl.d/60-vmovercommit.conf', 'vm.overcommit_memory = 1')


def kernel_thp_fix(c: Connection) -> None:
    # transparent_hugepage
    put(
        c,
        f'{config.local_assets_dir}/kernel/thp_fix_service',
        '/etc/systemd/system/thp_fix.service',
    )
    # Clean up stale symlinks from the old RequiredBy=docker.service install
    c.sudo('rm -f /etc/systemd/system/docker.service.requires/thp_fix.service')
    c.sudo('rm -f /etc/systemd/system/docker.service.wants/thp_fix.service')
    c.sudo('systemctl daemon-reload')
    c.sudo('systemctl enable thp_fix')
