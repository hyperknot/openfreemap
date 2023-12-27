#!/usr/bin/env bash

ruff check --fix .
ruff format .

find . -type f -name '*.conf' -path '*/nginx*' -exec nginxfmt -v {} +;


if [ -d "../styles" ]; then
  scripts/styles/lint_styles/lint_styles.py ../styles/
fi
