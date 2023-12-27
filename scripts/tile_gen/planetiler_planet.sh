#!/usr/bin/env bash
set -e

TILE_GEN_BIN=/data/ofm/tile_gen/bin

AREA=planet
DATE=$(date +"%Y%m%d_%H%M%S")
RUN_FOLDER="/data/ofm/tile_gen/runs/$AREA/${DATE}_pt"


mkdir -p "$RUN_FOLDER"
cd "$RUN_FOLDER" || exit

# the Xmx value below the most important parameter here
# 30 GB works well
java -Xmx30g \
  -jar $TILE_GEN_BIN/planetiler.jar \
  `# Download the latest planet.osm.pbf from s3://osm-pds bucket` \
  --area=planet --bounds=planet --download \
  `# Accelerate the download by fetching the 10 1GB chunks at a time in parallel` \
  --download-threads=10 --download-chunk-size-mb=1000 \
  `# Also download name translations from wikidata` \
  --fetch-wikidata \
  --output=tiles.mbtiles \
  `# Store temporary node locations at fixed positions in a memory-mapped file` \
  --nodemap-type=array --storage=mmap \
  --force \
  > planetiler.out 2> planetiler.err

rm -r data
echo planetiler.jar DONE

$TILE_GEN_BIN/extract_btrfs.sh