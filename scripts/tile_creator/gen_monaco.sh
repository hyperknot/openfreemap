#!/usr/bin/env bash

DATE=$(date +"%Y%m%d_%H%M%S")

RUN_FOLDER="/data/tile_creator/runs/monaco_$DATE"

mkdir -p "$RUN_FOLDER"
cd "$RUN_FOLDER" || exit

bash /data/tile_creator/bin/run_monaco.sh "$DATE"

