from setuptools import setup


requirements = [
    'fabric',
    'ruff',
    'python-dotenv',
]

setup(
    python_requires='>=3.10',
    install_requires=requirements,
    name='lib',
    packages=['lib'],
)
