#!/usr/bin/env bash
set -e

AREAS=('planet' 'monaco')

export RCLONE_CONFIG=rclone.conf


for AREA in "${AREAS[@]}"; do
  rclone lsf -R \
    --files-only \
    --fast-list \
    "cf:ofm-$AREA" > index.txt

  rclone lsf -R \
    --dirs-only \
    --dir-slash=false \
    --fast-list \
    "cf:ofm-$AREA" > dirs.txt

  rclone sync index.txt "cf:ofm-$AREA/a/b"
  rclone sync dirs.txt "cf:ofm-$AREA/c/d"
done



rclone copy \
  -vvv \
  --dump-bodies \
  --retries 1 \
  index.txt cf:ofm-monaco \
  2> out

