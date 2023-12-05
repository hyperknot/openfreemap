from setuptools import setup


requirements = [
    'fabric',
    'ruff',
    'python-dotenv',
]

setup(
    name='openfreemaps',
    python_requires='>=3.10',
    install_requires=requirements,
    packages=['ssh_lib'],
)
