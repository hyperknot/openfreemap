from ssh_lib.config import config
from ssh_lib.utils import apt_get_install, apt_get_purge, put, put_str


def setup_kernel_settings(c):
    put(c, f'{config}/sysctl/60-optim.conf', '/etc/sysctl.d/')


def set_cpu_governor(c):
    apt_get_install(c, 'cpufrequtils')
    apt_get_purge(c, 'linux-tools-*')
    # c.run('systemctl disable ondemand') # not working on 22

    put_str(
        c,
        '/etc/default/cpufrequtils',
        'GOVERNOR="performance"',
    )

    # check after reboot
    # cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
