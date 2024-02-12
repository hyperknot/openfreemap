## deduplicated on ext4

```df -h mnt_rw
df -h mnt_rw
Filesystem      Size  Used Avail Use% Mounted on
/dev/loop0      1.4T  187G  1.2T  14%
```

```
df -i mnt_rw
Filesystem        Inodes    IUsed     IFree IUse% Mounted on
/dev/loop0     393216000 39614466 353601534   11%
```
