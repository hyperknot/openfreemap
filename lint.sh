#!/usr/bin/env bash

prettier -w .

ruff check --fix .
ruff format .

find . -type f -name '*.conf' -path '*/nginx*' -exec nginxfmt -v {} +;



