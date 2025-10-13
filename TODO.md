logrotate

/var/log/nginx/*.log /var/log/nginx/*/*.log {
    daily                 # rotate at least once per day
    dateext               # add -YYYYMMDD to rotated files
    rotate 7              # keep up to 7 rotations (about 7 days)
    maxage 7              # hard limit: delete rotated logs older than 7 days
    missingok
    compress
    delaycompress
    notifempty
    sharedscripts
    create 0640 www-data adm   # adjust user:group for your distro (e.g., nginx adm)
    postrotate
        # Tell nginx to reopen logs without losing lines
        [ -s /run/nginx.pid ] && kill -USR1 "$(cat /run/nginx.pid)" || true
        # Alternatively: nginx -s reopen
    endscript
}

---

sudo systemctl enable --now logrotate.timer
sudo systemctl status logrotate.timer

/etc/cron.daily/logrotate 

Dry run:
sudo logrotate -d /etc/logrotate.d/nginx
Force a rotation immediately:
sudo logrotate -vf /etc/logrotate.conf

---

/var/log/nginx/*.log {
    daily           # Rotate every day
    rotate 7        # Keep only 7 rotated files
    missingok
    notifempty
    compress
    delaycompress
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 `cat /var/run/nginx.pid`
    endscript
}

---

