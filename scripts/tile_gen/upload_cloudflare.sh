#!/usr/bin/env bash
set -e

rclone sync \
  --transfers=8 \
  --multi-thread-streams=8 \
  --fast-list \
  -v \
  --stats-file-name-length 0 \
  --stats-one-line \
  --log-file rclone.log \
  20231208_091355_pt cf:ofm-planet

