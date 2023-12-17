# Comparing filesystem stats after extraction

Run: *planet_20231208*


## native mapbox/mbutil

Filesystem      1K-blocks       Used Available Use% Mounted on
/dev/loop0     1,474,386,100 1,119,622,516 354,763,584  76%

Filesystem        Inodes     IUsed     IFree IUse% Mounted on
/dev/loop0     393,216,000 269,252,174 123,963,826   69%


## deduplicated on ext4

39,570,683 dedupl files

df -h mnt_rw
Filesystem      Size  Used Avail Use% Mounted on
/dev/loop0      1.4T  187G  1.2T  14%

df mnt_rw
Filesystem      1K-blocks      Used  Available Use% Mounted on
/dev/loop0     1474386100 195624664 1278761436  14%

df -i mnt_rw
Filesystem        Inodes    IUsed     IFree IUse% Mounted on
/dev/loop0     393216000 39614466 353601534   11%


## deduplicated on BTRFS

### creation params

```
mkfs.btrfs -m single
mount -o noacl,nobarrier,noatime,max_inline=4096
```

### df

```
df -h mnt_rw
Filesystem      Size  Used Avail Use% Mounted on
/dev/loop3      300G  139G  161G  47%
```

```
df mnt_rw
Filesystem     1K-blocks      Used Available Use% Mounted on
/dev/loop3     314572800 145030788 168339820  47%
```

### btrfs

```
btrfs filesystem df mnt_rw
Data, single: total=48.01GiB, used=47.45GiB
System, single: total=4.00MiB, used=16.00KiB
Metadata, single: total=92.01GiB, used=90.37GiB
GlobalReserve, single: total=512.00MiB, used=0.00B
```


```
btrfs filesystem du -s mnt_rw
     Total   Exclusive  Set shared  Filename
  47.45GiB    47.45GiB       0.00B  mnt_rw
```
```
btrfs filesystem show mnt_rw
	Total devices 1 FS bytes used 137.81GiB
	devid    1 size 300.00GiB used 140.02GiB path /dev/loop3
```

```
btrfs filesystem usage mnt_rw
Overall:
    Device size:		 300.00GiB
    Device allocated:		 140.02GiB
    Device unallocated:		 159.98GiB
    Device missing:		     0.00B
    Used:			 137.81GiB
    Free (estimated):		 160.54GiB	(min: 160.54GiB)
    Free (statfs, df):		 160.54GiB
    Data ratio:			      1.00
    Metadata ratio:		      1.00
    Global reserve:		 512.00MiB	(used: 0.00B)
    Multiple profiles:		        no

Data,single: Size:48.01GiB, Used:47.45GiB (98.83%)
   /dev/loop3	  48.01GiB

Metadata,single: Size:92.01GiB, Used:90.37GiB (98.22%)
   /dev/loop3	  92.01GiB

System,single: Size:4.00MiB, Used:16.00KiB (0.39%)
   /dev/loop3	   4.00MiB

Unallocated:
   /dev/loop3	 159.98GiB
```

### compsize


```
compsize -x mnt_rw
Processed 308790063 files, 3458682 regular extents (6917363 refs), 301872700 inline.
Type       Perc     Disk Usage   Uncompressed Referenced  
TOTAL      100%      118G         118G         165G       
none       100%      118G         118G         165G       
```