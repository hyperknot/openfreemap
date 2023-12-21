#!/usr/bin/env bash

DATE=$(date +"%Y%m%d_%H%M%S")
TILE_GEN_BIN=/data/ofm/tile_gen/bin

RUN_FOLDER="/data/ofm/tile_gen/runs/monaco/${DATE}_pt"

mkdir -p "$RUN_FOLDER"
cd "$RUN_FOLDER" || exit

java -Xmx1g \
  -jar $TILE_GEN_BIN/planetiler.jar \
  `# Download the latest osm.pbf from s3://osm-pds bucket` \
  --area=monaco --download \
  `# Accelerate the download by fetching the 10 1GB chunks at a time in parallel` \
  --download-threads=10 --download-chunk-size-mb=1000 \
  `# Also download name translations from wikidata` \
  --fetch-wikidata \
  --output=tiles.mbtiles \
  `# Store temporary node locations at fixed positions in a memory-mapped file` \
  --nodemap-type=array --storage=mmap \
  --force \
  > "planetiler_out.log" 2> "planetiler_err.log"

