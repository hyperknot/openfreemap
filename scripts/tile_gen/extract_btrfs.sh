#!/usr/bin/env bash

sudo umount mnt || true
rm -rf mnt
rm -f image.btrfs


# make a sparse file
# make sure it's bigger then the current OSM output
fallocate -l 300G image.btrfs


mkfs.btrfs -v image.btrfs

# https://btrfs.readthedocs.io/en/latest/btrfs-man5.html#mount-options
# compression: zstd:1 or lzo

mkdir mnt
sudo mount -v \
  -t btrfs \
  -o noacl,nobarrier,noatime,compress-force=lzo,max_inline=4096 \
  image.btrfs mnt


sudo chown ofm:ofm -R mnt

../../tile_gen/venv/bin/python ../../tile_gen/extract.py output.mbtiles mnt/extract \
  > "extract_out.log" 2> "extract_err.log"

sudo umount mnt



