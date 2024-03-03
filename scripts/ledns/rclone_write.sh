#!/usr/bin/env bash

#env > /data/ofm/ledns/env.txt

RENEWED_DOMAINS=direct.openfreemap.org
RENEWED_LINEAGE=/etc/letsencrypt/live/ofm_ledns

rclone copy -v "$RENEWED_LINEAGE/fullchain.pem" "remote:ofm-secret/ledns/$RENEWED_DOMAINS/ofm_ledns.cert"
rclone copy -v "$RENEWED_LINEAGE/privkey.pem" "remote:ofm-secret/ledns/$RENEWED_DOMAINS/ofm_ledns.key"

