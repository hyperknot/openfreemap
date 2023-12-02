from openfreemaps.config import templates
from openfreemaps.utils import (
    apt_get_install,
    apt_get_purge,
    put,
    put_str,
)


def setup_time(c):
    apt_get_install(c, 'dbus')

    c.sudo('timedatectl set-local-rtc 0')
    c.sudo('timedatectl set-ntp 1')
    c.sudo('timedatectl set-timezone UTC')


def setup_kernel_settings(c):
    put(c, f'{templates}/sysctl/60-optim.conf', '/etc/sysctl.d/')



def set_cpu_governor(c):
    apt_get_install(c, 'cpufrequtils')
    apt_get_purge(c, 'linux-tools-*')

    put_str(
        c,
        '/etc/default/cpufrequtils',
        'GOVERNOR="performance"',
    )

    # check after reboot
    # cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
