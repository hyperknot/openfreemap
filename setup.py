from setuptools import find_packages, setup


requirements = [
    'click',
    'fabric',
    'nginxfmt',
    'python-dotenv',
    'ruff',
    'marko',
    'requests',
]


setup(
    python_requires='>=3.10',
    install_requires=requirements,
    packages=find_packages(),
)
