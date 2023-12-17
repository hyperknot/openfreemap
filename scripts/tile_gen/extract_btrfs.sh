#!/usr/bin/env bash

sudo umount mnt_rw || true
rm -rf mnt_rw
rm -f image.btrfs


# make an empty file that's definitely bigger then the current OSM output
fallocate -l 200G image.btrfs


# metadata: single needed as default is now DUP
mkfs.btrfs -v \
  -m single \
  image.btrfs

# https://btrfs.readthedocs.io/en/latest/btrfs-man5.html#mount-options
# compression doesn't make sense, data is already gzip compressed
mkdir -p mnt_rw
sudo mount -v \
  -t btrfs \
  -o noacl,nobarrier,noatime,max_inline=4096 \
  image.btrfs mnt_rw


sudo chown ofm:ofm -R mnt_rw

../../tile_gen/venv/bin/python ../../tile_gen/extract_mbtiles.py output.mbtiles mnt_rw/extract \
  > "extract_out.log" 2> "extract_err.log"

sudo umount mnt_rw

sudo ../../tile_gen/venv/bin/python ../../tile_gen/shrink_btrfs.py image.btrfs \
  > "shrink_out.log" 2> "shrink_err.log"

# pigz -k image.btrfs --fast

# rsync -avH mnt_rw/extract/ mnt_rw2/extract/ > rsync_out.log 2> rsync_err.log