#!/usr/bin/env bash

#env > /data/ofm/ledns/env.txt
#RENEWED_DOMAINS=direct.openfreemap.org
#RENEWED_LINEAGE=/etc/letsencrypt/live/ofm_ledns

export RCLONE_CONFIG=/data/ofm/config/rclone.conf

rclone copyto -v --copy-links "$RENEWED_LINEAGE/fullchain.pem" "remote:ofm-private/ledns/$RENEWED_DOMAINS/ofm_ledns.cert"
rclone copyto -v --copy-links "$RENEWED_LINEAGE/privkey.pem" "remote:ofm-private/ledns/$RENEWED_DOMAINS/ofm_ledns.key"

