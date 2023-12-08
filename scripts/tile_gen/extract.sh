#!/usr/bin/env bash

# reference:
# https://www.kernel.org/doc/Documentation/filesystems/ext4.txt
# https://wiki.archlinux.org/title/ext4
#
# -m reserved-blocks-percentage
# -F Force mke2fs to create a filesystem, even if the specified device is not a partition on a block special device
#
# -O feature
# from  /etc/mke2fs.conf
# defaults: has_journal,extent,huge_file,flex_bg,metadata_csum,64bit,dir_nlink,extra_isize
# disabling journalling, since it's a read-only fs, as well as other unused features
#
# -E extended-options
# lazy_itable_init - inode table is fully initialized at the time of file system creation
# nodiscard - Do not attempt to discard blocks at mkfs time.
#
# -T news or small


sudo umount mnt || true
rm -rf mnt
rm -f image.ext4


# make a sparse file
# make sure it's bigger then the current OSM output
# less fragmentation with fallocate
fallocate -l 1500G image.ext4
#truncate -s 1500G image.ext4


mke2fs -t ext4 -v \
  -m 0 \
  -F \
  -O ^has_journal,^extent,^huge_file,^metadata_csum,^64bit,^extra_isize \
  -E lazy_itable_init=0,nodiscard \
  -T small \
  image.ext4

mkdir mnt
sudo mount -v \
  -t ext4 \
  -o nobarrier,noatime \
  image.ext4 mnt

sudo chown ofm:ofm -R mnt

../../tile_gen/venv/bin/python ../../tile_gen/extract.py output.mbtiles mnt/extract \
  > "extract_out.log" 2> "extract_err.log"

sudo umount mnt

resize2fs -M image.ext4
e2fsck -vf image.ext4

#fsck.ext4 -f -C 0 /dev/sda1;
#
#filefrag -e image.ext4
#
#tune2fs -E mount_opts=ro image.ext4
#
#cp --sparse=never sparsefile regularfile
#



