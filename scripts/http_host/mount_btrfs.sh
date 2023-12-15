mkdir -p mnt_ro
sudo mount -v \
  -t btrfs \
  -o ro \
  image.btrfs mnt_ro