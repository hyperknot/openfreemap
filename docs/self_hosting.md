# Self-hosting Howto

You can either self-host or use our public instance. Everything is **open-source**, including the full production setup — there’s no 'open-core' model here.

When self-hosting, there are two modules you can set up on a server (see details in the repo README).

- **linux-host**

- **tilegen**

There is a 99.9% chance you only need **linux-host**. Tile-gen is slow, needs a huge machine and is totally pointless, since we upload the processed files every week.

### System requirements

**linux-host**: 300 GB disk space for hosting a single run. SSD is recommended, but not required.

**tilegen**: 500 GB SDD and at least 64 GB ram

**Ubuntu 24.04**

### Provider recommendation

One amazing deal, which is tested and known to work well for linux-host is the €4.5 / month [Contabo Storage VPS](https://contabo.com/en/storage-vps/)

---

### Warning

This project is made to run on **clean servers** or virtual machines dedicated for this project. The scripts need sudo permissions as they mount/unmount disk images. Do not run this on your dev machine without using virtual machines. If you do, please make sure you understand exactly what each script is doing.

If you run it on a non-clean server, please understand that this will modify your nginx config!

---

## Instructions

I recommend running things quickly first, with `SKIP_PLANET=true` and then once it works, running it with `SKIP_PLANET=false`.

#### 1. DNS setup

Set up a server with at least 300 GB SSD space and configure the DNS for the subdomain of your choice.
For example, make an A record for "maps.example.com" -> 185.199.110.153

#### 2. Clone and prepare `config` folder

```
git clone https://github.com/hyperknot/openfreemap
```

In the config folder, copy `.env.sample` to `.env` and set the values.

`DOMAIN_DIRECT` - Your subdomain \
`LETSENCRYPT_EMAIL` - Your email for Let's Encrypt

Set `SKIP_PLANET=true` first.

#### 3. Set up Python if you don't have it yet

Install [uv](https://docs.astral.sh/uv/) locally and make sure it is on your `PATH`.

#### 4. Prepare the Python environment

You run the deploy script locally, and it deploys to a remote server over SSH. You can use a virtualenv if you are used to working with them, but it's not necessary.

```
cd openfreemap
uv sync
```

#### 5. Deploy quick version with `SKIP_PLANET=true`

Run the actual deploy command and wait a few minutes:

```
./linux_host/deploy_linux_host.py init-static HOSTNAME
```

The deploy script connects over SSH. You can SSH as `root` or as a normal sudo-capable user; the script creates and uses an `ofm` runtime user. If needed, add `--user YOUR_SSH_USER` and/or `--port 22`.

For password-based SSH, set `SSH_PASSWD`. If sudo uses a different password, set `SUDO_PASSWD` too:

```
SSH_PASSWD='your-ssh-password' SUDO_PASSWD='your-sudo-password' ./linux_host/deploy_linux_host.py --user YOUR_SSH_USER --port 22 init-static HOSTNAME
```

#### 5. Check

If everything is OK, you'll have some curl lines printed. Run the first one locally and make sure it's showing HTTP/2 200. For example this is an OK response.

```locally to test them.
curl -sI https://test.openfreemap.org/monaco

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

#### 6. Deploy and check with `SKIP_PLANET=false`

Update your `.env` file and re-run the same `./linux_host/deploy_linux_host.py init-static HOSTNAME` as before.

Go for a walk and by the time you come back it should be up and running with the latest planet tiles deployed. Don't worry about the "Download aborted" lines in the meanwhile, it's a bug in CloudFlare.

If your server doesn't have an SSD, the download + uncompressing process can take hours.

---

#### Deploy tilegen server (optional)

If you have a really beefy machine (see above) and you really want to generate tiles yourself:

```
./tilegen/deploy_tilegen.py HOSTNAME
```

The same `--user`, `--port`, `SSH_PASSWD` and `SUDO_PASSWD` options from the linux-host deploy also work here. Add `--cron` to enable the tilegen cron job.

Trigger a run manually over SSH:

```
cd /data/ofm/src && ./tilegen/scripts/tilegen.py make-tiles planet --upload
```

For a quick smoke test, use `monaco` instead of `planet`. It's recommended to use tmux or similar, as a full planet run can take days to complete.
