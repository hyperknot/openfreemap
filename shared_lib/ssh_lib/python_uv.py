from .utils import exists


UV_BIN = '/usr/local/bin'


def python_uv(c, install_python_ver=None):
    """Install Python using uv package manager."""

    # Clean up old root-only install
    c.sudo('rm -f /root/.local/bin/uv /root/.local/bin/uvx', warn=True)

    # Install uv globally so all users can access it
    if not exists(c, f'{UV_BIN}/uv'):
        c.sudo(
            f"env UV_UNMANAGED_INSTALL='{UV_BIN}' sh -c 'curl -LsSf https://astral.sh/uv/install.sh | sh'"
        )

    # Install Python using uv
    if install_python_ver:
        c.run(f'{UV_BIN}/uv python install {install_python_ver} --default')
