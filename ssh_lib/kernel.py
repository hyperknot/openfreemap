from ssh_lib.config import ASSETS_DIR
from ssh_lib.utils import put


def setup_kernel_settings(c):
    put(c, f'{ASSETS_DIR}/kernel/60-ofm.conf', '/etc/sysctl.d/')
    put(c, f'{ASSETS_DIR}/kernel/limits-ofm.conf', '/etc/security/limits.d/')
