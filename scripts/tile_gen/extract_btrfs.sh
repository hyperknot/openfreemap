#!/usr/bin/env bash
set -e

sudo umount mnt_rw || true
sudo umount mnt_rw2 || true
rm -rf mnt_rw*
rm -f image*.btrfs
rm -f *.log

# make an empty file that's definitely bigger then the current OSM output
fallocate -l 200G image.btrfs
fallocate -l 200G image2.btrfs


# metadata: single needed as default is now DUP
mkfs.btrfs -v \
  -m single \
  image.btrfs

mkfs.btrfs -v \
  -m single \
  image2.btrfs

# https://btrfs.readthedocs.io/en/latest/btrfs-man5.html#mount-options
# compression doesn't make sense, data is already gzip compressed
mkdir -p mnt_rw mnt_rw2

sudo mount -v \
  -t btrfs \
  -o noacl,nobarrier,noatime,max_inline=4096 \
  image.btrfs mnt_rw

sudo mount -v \
  -t btrfs \
  -o noacl,nobarrier,noatime,max_inline=4096 \
  image.btrfs mnt_rw2

sudo chown ofm:ofm -R mnt_rw mnt_rw2

../../tile_gen/venv/bin/python ../../tile_gen/extract_mbtiles.py output.mbtiles mnt_rw/extract \
  > extract_out.log 2> extract_err.log

# we need to extract, delete and rsync onto a new partition
# otherwise the partition image stays big
rsync -aH mnt_rw/extract/ mnt_rw2/extract/ > rsync_out.log 2> rsync_err.log

sudo umount mnt_rw
sudo umount mnt_rw2
rm -r mnt_rw*

sudo ../../tile_gen/venv/bin/python ../../tile_gen/shrink_btrfs.py image2.btrfs \
  > shrink_out.log 2> shrink_err.log


#rm image.btrfs

#mv image2.btrfs done.btrfs

# pigz -k image.btrfs --fast

