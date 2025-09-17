from ssh_lib import ASSETS_DIR
from ssh_lib.utils import put, put_str


def kernel_somaxconn65k(c):
    put_str(c, '/etc/sysctl.d/60-somaxconn65k.conf', 'net.core.somaxconn = 65535')


def kernel_limits1m(c):
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


def kernel_vmovercommit(c):
    put_str(c, '/etc/sysctl.d/60-vmovercommit.conf', 'vm.overcommit_memory = 1')


def kernel_thp_fix(c):
    # transparent_hugepage
    put(c, f'{ASSETS_DIR}/kernel/thp_fix_service', '/etc/systemd/system/thp_fix.service')
    c.sudo('systemctl daemon-reload')
    c.sudo('systemctl enable thp_fix')
