#!/usr/bin/env bash

find . -name "*.egg-info" -exec rm -rf {} +
find . -name __pycache__ -exec rm -rf {} +

# deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate

pip install -U pip wheel setuptools

pip install -e .
pip install -e modules/http_host
pip install -e modules/tile_gen
pip install -e modules/loadbalancer



