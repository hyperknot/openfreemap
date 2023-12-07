from setuptools import setup


requirements = ['fabric', 'ruff', 'python-dotenv', 'click']

setup(
    name='openfreemap',
    python_requires='>=3.10',
    install_requires=requirements,
    packages=['ssh_lib'],
)
