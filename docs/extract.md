### native mapbox/mbutil

Filesystem      1K-blocks       Used Available Use% Mounted on
/dev/loop0     1,474,386,100 1,119,622,516 354,763,584  76%

Filesystem        Inodes     IUsed     IFree IUse% Mounted on
/dev/loop0     393,216,000 269,252,174 123,963,826   69%



### extract dedupl ext4

39,570,683 dedupl files

df -h mnt
Filesystem      Size  Used Avail Use% Mounted on
/dev/loop0      1.4T  187G  1.2T  14%

df mnt
Filesystem      1K-blocks      Used  Available Use% Mounted on
/dev/loop0     1474386100 195624664 1278761436  14%

df -i mnt
Filesystem        Inodes    IUsed     IFree IUse% Mounted on
/dev/loop0     393216000 39614466 353601534   11%

--- after resize2fs ext4

df -h mnt
Filesystem      Size  Used Avail Use% Mounted on
/dev/loop0      189G  187G  2.4G  99%

df mnt
Filesystem     1K-blocks      Used Available Use% Mounted on
/dev/loop0     198098376 195624664   2473712  99%

df -i mnt
Filesystem       Inodes    IUsed    IFree IUse% Mounted on
/dev/loop0     52854784 39614466 13240318   75%


### extract dedupl btrfs
note: this test uses compress-force=lzo, but it's actually uncompressible data since the PBF files are gzipped already


df -h mnt
Filesystem      Size  Used Avail Use% Mounted on
/dev/loop0      300G   97G  204G  33%

df mnt
Filesystem     1K-blocks      Used Available Use% Mounted on
/dev/loop0     314572800 100925972 213428604  33%

btrfs filesystem df mnt
Data, single: total=48.01GiB, used=47.45GiB
System, single: total=4.00MiB, used=16.00KiB
Metadata, single: total=49.01GiB, used=48.32GiB
GlobalReserve, single: total=496.86MiB, used=0.00B

btrfs filesystem du -s mnt
     Total   Exclusive  Set shared  Filename
  47.45GiB    47.45GiB       0.00B  mnt


sudo btrfs filesystem show mnt
Label: none  uuid: ce7615d1-0ee5-460b-bdb0-7c4d214eecc4
        Total devices 1 FS bytes used 95.76GiB
        devid    1 size 300.00GiB used 97.02GiB path /dev/loop0

sudo btrfs filesystem usage mnt
Overall:
    Device size:                 300.00GiB
    Device allocated:             97.02GiB
    Device unallocated:          202.98GiB
    Device missing:                  0.00B
    Used:                         95.76GiB
    Free (estimated):            203.54GiB      (min: 203.54GiB)
    Free (statfs, df):           203.54GiB
    Data ratio:                       1.00
    Metadata ratio:                   1.00
    Global reserve:              501.22MiB      (used: 0.00B)
    Multiple profiles:                  no

Data,single: Size:48.01GiB, Used:47.45GiB (98.83%)
   /dev/loop0     48.01GiB

Metadata,single: Size:49.01GiB, Used:48.32GiB (98.60%)
   /dev/loop0     49.01GiB

System,single: Size:4.00MiB, Used:16.00KiB (0.39%)
   /dev/loop0      4.00MiB

Unallocated:
   /dev/loop0    202.98GiB



compsize -x mnt
Processed 44249086 files, 3458702 regular extents (3800454 refs), 40448654 inline.
Type       Perc     Disk Usage   Uncompressed Referenced
TOTAL       99%       74G          74G          80G
none       100%       74G          74G          80G
lzo         20%      4.0K          20K          20K

