#!/usr/bin/env bash

find . -name "*.egg-info" -exec rm -rf {} +
find . -name __pycache__ -exec rm -rf {} +

# deactivate
rm -rf venv
python3 -m venv venv

venv/bin/pip -V

venv/bin/pip install -U pip wheel setuptools
venv/bin/pip install git+https://github.com/mapbox/mbutil.git@544c76e




