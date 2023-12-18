#!/usr/bin/env bash
set -e

sudo umount mnt_rw 2> /dev/null || true
sudo umount mnt_rw2 2> /dev/null || true
rm -rf mnt_rw* tmp_*
rm -f *.btrfs *.gz
rm -f *.log

# make an empty file that's definitely bigger then the current OSM output
fallocate -l 200G image.btrfs
fallocate -l 200G image2.btrfs


# metadata: single needed as default is now DUP
mkfs.btrfs \
  -m single \
  image.btrfs > /dev/null

mkfs.btrfs \
  -m single \
  image2.btrfs > /dev/null

# https://btrfs.readthedocs.io/en/latest/btrfs-man5.html#mount-options
# compression doesn't make sense, data is already gzip compressed
mkdir -p mnt_rw mnt_rw2

sudo mount \
  -t btrfs \
  -o noacl,nobarrier,noatime,max_inline=4096 \
  image.btrfs mnt_rw

sudo mount \
  -t btrfs \
  -o noacl,nobarrier,noatime,max_inline=4096 \
  image2.btrfs mnt_rw2

sudo chown ofm:ofm -R mnt_rw mnt_rw2

../../tile_gen/venv/bin/python ../../tile_gen/extract_mbtiles.py output.mbtiles mnt_rw/extract \
  > extract_out.log 2> extract_err.log

grep fixed extract_out.log > dedupl_fixed.log || true

# we need to extract, delete dedupl and rsync onto a new partition
# otherwise the partition image stays big
rsync -avH mnt_rw/extract/ mnt_rw2/extract/ > rsync_out.log 2> rsync_err.log


# collect stats
{
echo -e "df -h"
sudo df -h mnt_rw2

echo -e "\n\nbtrfs filesystem df"
sudo btrfs filesystem df mnt_rw2

echo -e "\n\nbtrfs filesystem show"
sudo btrfs filesystem show mnt_rw2

echo -e "\n\nbtrfs filesystem usage"
sudo btrfs filesystem usage mnt_rw2

echo -e "\n\nbtrfs filesystem du -s"
sudo btrfs filesystem du -s mnt_rw2

echo -e "\n\ncompsize -x"
sudo compsize -x mnt_rw2 2> /dev/null || true
} > stats.txt


sudo umount mnt_rw
sudo umount mnt_rw2
rm -r mnt_rw*

sudo ../../tile_gen/venv/bin/python ../../tile_gen/shrink_btrfs.py image2.btrfs \
  > shrink_out.log 2> shrink_err.log


rm image.btrfs
mv image2.btrfs done.btrfs

pigz done.btrfs --fast

echo DONE
