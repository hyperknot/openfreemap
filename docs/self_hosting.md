# Self-hosting Howto

You can either self-host or use our public instance. Everything is **open-source**, including the full production setup — there’s no 'open-core' model here.

When self-hosting, there are two modules you can set up on a server (see details in the repo README).

- **linux_host**

- **tilegen**

There is a 99.9% chance you only need **linux_host**. tilegen is slow, needs a huge machine and is totally pointless, since we upload the processed files every week.

### System requirements

**linux_host**: 300 GB disk space for hosting a single planet run. SSD is recommended, but not required. Note that an `auto_update: true` host may hold TWO complete versions during a release transition (the active version plus a prefetched candidate), so provide capacity for two complete versions on automatic planet hosts.

**tilegen**: 500 GB SDD and at least 64 GB ram

**Ubuntu 24.04 or newer**

### Provider recommendation

One amazing deal, which is tested and known to work well for linux_host is the €4.5 / month [Contabo Storage VPS](https://contabo.com/en/storage-vps/)

---

### Warning

This project is made to run on **clean servers** or virtual machines dedicated for this project. The scripts need sudo permissions as they mount/unmount disk images. Do not run this on your dev machine without using virtual machines. If you do, please make sure you understand exactly what each script is doing.

If you run it on a non-clean server, please understand that this will modify your nginx config!

---

## Instructions

I recommend running things quickly first, with `"areas": ["monaco"]` and then once it works, running it with `"areas": ["planet", "monaco"]`.

#### 1. DNS setup

Set up a server with at least 300 GB SSD space and configure the DNS for the subdomain of your choice.
For example, make an A record for "maps.example.com" -> 185.199.110.153

#### 2. Clone and prepare `config` folder

```
git clone https://github.com/hyperknot/openfreemap
cd openfreemap
cp config/linux_host/config.sample.jsonc config/linux_host/self-hosted.jsonc
```

Edit `config/linux_host/self-hosted.jsonc` and fill it out:

- replace `tiles.example.com` with your own domain
- choose a certificate type: `letsencrypt` (set your `email`), `upload` (provide your cert/key files), or `dummy` for local testing only — see the comments in the sample
- set `hosts` to your SSH alias(es)
- set `auto_update`: `true` follows new releases; `false` pins the host to the version deployed at setup time, with no network access after the first successful sync
- set `areas`: use `["monaco"]` for the first quick deploy, then `["planet", "monaco"]` for the full deploy

#### 3. Set up Python if you don't have it yet

Install [uv](https://docs.astral.sh/uv/) locally and make sure it is on your `PATH`.

#### 4. Prepare the Python environment

You run the deploy script locally, and it deploys to a remote server over SSH. You can use a virtualenv if you are used to working with them, but it's not necessary.

```
uv sync
```

#### 5. Deploy quick version with `"areas": ["monaco"]`

Run the actual deploy command. The config name maps to `config/linux_host/self-hosted.jsonc`:

```
./linux_host/deploy_linux_host.py --config self-hosted
```

This targets every host listed in the config's `hosts` array. To target a single host, pass its alias:

```
./linux_host/deploy_linux_host.py --config self-hosted --host HOSTNAME
```

The deploy script connects over SSH. You can SSH as `root` or as a normal sudo-capable user; the script creates and uses an `ofm` runtime user. If needed, add `--user YOUR_SSH_USER` and/or `--port 22`.

Deployment takes each target host offline while it rebuilds the serving setup. It disables scheduling, stops sync and nginx processes, unmounts images, and recreates disposable runtime state. It preserves downloaded assets, nginx ACME state, and complete images for configured areas. It removes images for areas that are no longer configured.

For password-based SSH, set `SSH_PASSWD`. If sudo uses a different password, set `SUDO_PASSWD` too:

```
SSH_PASSWD='your-ssh-password' SUDO_PASSWD='your-sudo-password' ./linux_host/deploy_linux_host.py --config self-hosted --host HOSTNAME --user YOUR_SSH_USER --port 22
```

#### 6. Check

Deployment is asynchronous: the deploy command does not print curl lines and does not wait for tiles to become live. It prints a success message and a MapLibre style URL, `https://YOUR_DOMAIN/styles/liberty`.

Every host gets a once-per-minute sync cron, so the first download starts within a minute. Follow it with `tail -f /data/ofm/linux_host/logs/linux_host_sync.log` on the host.

Once the sync has finished, verify it yourself. Run this locally and make sure it shows HTTP/2 200. For example this is an OK response:

```
curl -sI https://YOUR_DOMAIN/monaco

HTTP/2 200
access-control-allow-origin: *
cache-control: max-age=86400
cache-control: public
content-length: 5776
content-type: application/json
date: Fri, 11 Oct 2024 21:01:23 GMT
etag: "670991d1-1690"
expires: Sat, 12 Oct 2024 21:01:23 GMT
last-modified: Fri, 11 Oct 2024 21:00:01 GMT
server: nginx
x-ofm-debug: latest JSON monaco
```

`https://YOUR_DOMAIN/planet/latest` always points to the active deployed Planet TileJSON, and `/planet/latest/{z}/{x}/{y}.pbf` serves its tiles. Any non-existing version also serves the active version. `/planet/latest` and non-existing version responses may be cached for up to 1 day; specific version URLs are cached long term.

### Synchronization and retained versions

A sync keeps the active deployed version available while it downloads and verifies a replacement in full. Verified images live under `versions/`. Each download starts from zero in a disposable `tmp/` directory; downloads are not resumed.

Sync runs every minute on every host. Each run:

1. Mounts every complete image on disk and starts nginx. With `auto_update: false`, the run stops here after the first successful sync, so the host needs no network access afterwards.
2. Reads the deployed versions and `files.txt` from Cloudflare.
3. Downloads the deployed versions.
4. With `auto_update: true`, downloads the newest completed version as a candidate.
5. Mounts the images, reloads nginx if its config changed and `nginx -t` passes, then removes versions no longer needed.
6. Downloads the assets.

A Cloudflare failure (request error, invalid content, failed download) ends the run with a `cloudflare: ...; retrying next minute` line, and the next run tries again.

nginx is disabled at boot; after a reboot, the first sync mounts the images and starts it. If you stop nginx manually, the next sync starts it again; remove `/etc/cron.d/ofm_linux_host` to keep it stopped.

Telegram is optional (`telegram_token`, `telegram_chat_id`, `telegram_topic_id`). It sends silent messages for each download and version switch. Repeated downloads of the same version (tracked in `/data/ofm/linux_host/download_ledger.txt`) notify with sound. Other errors (mount, nginx, disk space, SHA-256 mismatch, failed candidate) alert on every run until fixed.

#### 7. Deploy and check with `"areas": ["planet", "monaco"]`

Edit `config/linux_host/self-hosted.jsonc` to set `"areas": ["planet", "monaco"]` and re-run the same `./linux_host/deploy_linux_host.py --config self-hosted [--host HOSTNAME]` as before.

Go for a walk and by the time you come back it should be up and running with the latest planet tiles deployed. Don't worry about `cloudflare: ...; retrying next minute` lines in the meantime; a failed download restarts from zero on the next run.

If your server doesn't have an SSD, the download + uncompressing process can take hours.

---

#### Deploy tilegen server (optional)

If you have a really beefy machine (see above) and you really want to generate tiles yourself:

Copy the tilegen sample config to a named config first:

```
cp config/tilegen/config.sample.jsonc config/tilegen/self-hosted.jsonc
```

Set `cron` to `true` only if this host should run automated tile builds, uploads, version publication, and index refreshes. Then deploy using the config name that maps to `config/tilegen/self-hosted.jsonc`:

```
./tilegen/deploy_tilegen.py --config self-hosted [--host HOSTNAME]
```

The same `--user`, `--port`, `SSH_PASSWD` and `SUDO_PASSWD` options from the linux_host deploy also work here. Each deployment installs or removes the tilegen cron job according to the config.

A normal deployment refuses to make any server change if a `make-tiles` build is running.

Reinstall stops all tilegen commands and their child processes, verifies that they stopped, unmounts and verifies filesystems below `/data/ofm`, and then removes `/data/ofm`. `/data/ofm_keep` (Wikidata cache) is never deleted.

Trigger a run manually over SSH as the `ofm` runtime user:

```
cd /data/ofm/src && sudo -u ofm env PYTHONUNBUFFERED=1 ./tilegen/scripts/tilegen.py make-tiles planet --upload
```

Running as `ofm` keeps manual and scheduled build files under the same ownership.

For a quick smoke test, use `monaco` instead of `planet`. It's recommended to use tmux or similar, as a full planet run can take days to complete.
