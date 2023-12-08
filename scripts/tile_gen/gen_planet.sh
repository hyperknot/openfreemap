#!/usr/bin/env bash

DATE=$(date +"%Y%m%d_%H%M%S")

RUN_FOLDER="/data/ofm/runs/planet_$DATE"

mkdir -p "$RUN_FOLDER"
cd "$RUN_FOLDER" || exit

bash /data/ofm/tile_gen/planetiler_planet.sh "$DATE"

