#!/usr/bin/env bash

# these are not needed as certbot generates these
#env > /data/ofm/roundrobin/env.txt
#RENEWED_DOMAINS=direct.openfreemap.org
#RENEWED_LINEAGE=/etc/letsencrypt/live/ofm_roundrobin

export RCLONE_CONFIG=/data/ofm/config/rclone.conf

rclone copyto -v --copy-links "$RENEWED_LINEAGE/fullchain.pem" "remote:ofm-private/roundrobin/$RENEWED_DOMAINS/ofm_roundrobin.cert"
rclone copyto -v --copy-links "$RENEWED_LINEAGE/privkey.pem" "remote:ofm-private/roundrobin/$RENEWED_DOMAINS/ofm_roundrobin.key"

