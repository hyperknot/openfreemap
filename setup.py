from setuptools import setup


requirements = ['fabric', 'ruff']

setup(
    python_requires='>=3.10',
    install_requires=requirements,
    name='openfreemaps',
    packages=['openfreemaps'],
)
