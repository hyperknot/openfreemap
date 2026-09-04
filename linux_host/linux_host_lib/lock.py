import fcntl
import sys
from collections.abc import Iterator
from contextlib import contextmanager

from linux_host.linux_host_lib.linux_host_config import get_linux_host_config


@contextmanager
def host_lock() -> Iterator[None]:
    """Single lock for all state-changing linux_host operations."""
    get_linux_host_config().lock_file.parent.mkdir(parents=True, exist_ok=True)
    fp = open(get_linux_host_config().lock_file, 'w')
    try:
        fcntl.flock(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print('sync skipped: another instance holds the lock')
        sys.exit(0)
    try:
        yield
    finally:
        fp.close()
