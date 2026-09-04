import fcntl
import sys
from collections.abc import Iterator
from contextlib import contextmanager

from tilegen.tilegen_lib.tilegen_config import get_tilegen_config


@contextmanager
def tile_build_lock() -> Iterator[None]:
    """Prevent concurrent tile builds on this host."""
    # One host-wide lock covers the full pipeline. Planet and Monaco are both too
    # resource-heavy for per-area concurrency.
    lock_file = get_tilegen_config().tilegen_dir / 'make_tiles.lock'
    lock_file.parent.mkdir(parents=True, exist_ok=True)

    with lock_file.open('w') as fp:
        try:
            fcntl.flock(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('make-tiles skipped: another tile build holds the lock')
            sys.exit(0)

        yield
