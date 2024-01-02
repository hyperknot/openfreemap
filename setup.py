from setuptools import setup


requirements = [
    'click',
    'fabric',
    'nginxfmt',
    'python-dotenv',
    'requests',
    'ruff',
]

setup(
    python_requires='>=3.10',
    install_requires=requirements,
    packages=['ssh_lib'],
)
