#!/usr/bin/env bash
set -e

DIR_NAME="${PWD##*/}"

rm -f rclone.log

rclone sync \
  --transfers=8 \
  --multi-thread-streams=8 \
  --fast-list \
  -v \
  --stats-file-name-length 0 \
  --stats-one-line \
  --log-file rclone.log \
  --exclude rclone.log \
  . "cf:ofm-planet/$DIR_NAME"

