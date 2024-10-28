#!/usr/bin/env bash

export ENV=prod

./init-server.py http-host-sync ofm-h-fi-1 -y
./init-server.py http-host-sync ofm-h-de-2 -y

