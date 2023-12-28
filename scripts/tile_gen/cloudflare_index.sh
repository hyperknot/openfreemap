#!/usr/bin/env bash
set -e

AREAS=('planet' 'monaco')

export RCLONE_CONFIG=/data/ofm/config/rclone.conf

rm -rf index
mkdir index

for AREA in "${AREAS[@]}"; do
  rclone lsf -R \
    --files-only \
    --fast-list \
    --exclude dirs.txt \
    --exclude index.txt \
    "cf:ofm-$AREA" > index/index.txt

  rclone lsf -R \
    --dirs-only \
    --dir-slash=false \
    --fast-list \
    "cf:ofm-$AREA" > index/dirs.txt

  rclone copy index "cf:ofm-$AREA"
done

rm -rf index
