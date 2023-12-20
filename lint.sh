#!/usr/bin/env bash

ruff check --fix .
ruff format .

# https://github.com/soulteary/nginx-formatter
nginx-formatter
