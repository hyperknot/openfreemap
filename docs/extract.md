### native mapbox/mbutil

Filesystem      1K-blocks       Used Available Use% Mounted on
/dev/loop0     1,474,386,100 1,119,622,516 354,763,584  76% /data/ofm/runs/planet_20231208_091355/mnt

Filesystem        Inodes     IUsed     IFree IUse% Mounted on
/dev/loop0     393,216,000 269,252,174 123,963,826   69% /data/ofm/runs/planet_20231208_091355/mnt



### extract dedupl ext4

39,570,683 dedupl files

df -h mnt
Filesystem      Size  Used Avail Use% Mounted on
/dev/loop0      1.4T  187G  1.2T  14% /data/ofm/runs/planet_20231208_091355/mnt

df mnt
Filesystem      1K-blocks      Used  Available Use% Mounted on
/dev/loop0     1474386100 195624664 1278761436  14% /data/ofm/runs/planet_20231208_091355/mnt

df -i mnt
Filesystem        Inodes    IUsed     IFree IUse% Mounted on
/dev/loop0     393216000 39614466 353601534   11% /data/ofm/runs/planet_20231208_091355/mnt

--- after resize2fs ext4

df -h mnt
Filesystem      Size  Used Avail Use% Mounted on
/dev/loop0      189G  187G  2.4G  99% /data/ofm/runs/planet_20231208_091355/mnt

df mnt
Filesystem     1K-blocks      Used Available Use% Mounted on
/dev/loop0     198098376 195624664   2473712  99% /data/ofm/runs/planet_20231208_091355/mnt

df -i mnt
Filesystem       Inodes    IUsed    IFree IUse% Mounted on
/dev/loop0     52854784 39614466 13240318   75% /data/ofm/runs/planet_20231208_091355/mnt



