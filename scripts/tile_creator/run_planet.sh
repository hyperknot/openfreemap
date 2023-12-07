#!/usr/bin/env bash

# the Xmx value below the most important parameter here
# setting is less then 25g means there is too little memory
# setting it to too much means there is too much memory used

java -Xmx30g \
  -jar /data/ofm/tile_creator/bin/planetiler.jar \
  `# Download the latest planet.osm.pbf from s3://osm-pds bucket` \
  --area=planet --bounds=planet --download \
  `# Accelerate the download by fetching the 10 1GB chunks at a time in parallel` \
  --download-threads=10 --download-chunk-size-mb=1000 \
  `# Also download name translations from wikidata` \
  --fetch-wikidata \
  --output=output.mbtiles \
  `# Store temporary node locations at fixed positions in a memory-mapped file` \
  --nodemap-type=array --storage=mmap \
  --force \
  > "output.log" 2> "err.log"



