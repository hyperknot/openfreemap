#!/usr/bin/env bash

sudo umount mnt || true
rm -rf mnt
rm -f image.btrfs


# make a sparse file
# make sure it's bigger then the current OSM output
fallocate -l 300G image.btrfs

fallocate -l 10G image.btrfs





# metadata: single needed as default is now DUP
mkfs.btrfs -v \
  -m single \
  image.btrfs

# https://btrfs.readthedocs.io/en/latest/btrfs-man5.html#mount-options
# compression doesn't make sense, data is already gzip compressed

mkdir -p mnt
sudo mount -v \
  -t btrfs \
  -o noacl,nobarrier,noatime,max_inline=4096 \
  image2.btrfs mnt


sudo chown ofm:ofm -R mnt

../../tile_gen/venv/bin/python ../../tile_gen/extract.py output.mbtiles mnt/extract \
  > "extract_out.log" 2> "extract_err.log"


# resize to min possible size
btrfs filesystem usage -b mnt

btrfs filesystem resize -10G mnt
sudo btrfs filesystem resize -100M mnt


sudo umount mnt




