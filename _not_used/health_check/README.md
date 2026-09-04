# Unused health-check implementation

This directory preserves the health-check implementation that was removed from the active application because health checking is outside the branch scope.

Original locations:

- `server_health.py`: `shared_lib/utils/server_health.py`
- `pycurl.py`: `shared_lib/utils/pycurl.py`
- `get_ip_from_ssh_alias.py`: `shared_lib/ssh_lib/utils.py::get_ip_from_ssh_alias`

The implementation used the runtime dependency `pycurl>=7.45.7`. It had no CLI, deployment hook, cron task, or other caller.
