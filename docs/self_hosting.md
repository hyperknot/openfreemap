# Self-hosting Howto

You can either self-host or use our public instance. Everything is **open-source**, including the full production setup — there’s no 'open-core' model here.

When self-hosting, there are two modules you can set up on a server (see details in the repo README).

- **http-host**

- **tile-gen**

I there is a 99.9% chance you only need **http-host**. Tile-gen is slow, needs a huge machine and is totally pointless, since we upload the processed files every week.

### System requirements

**http-host**: 300 GB SSD for hosting a single run and 4 GB RAM

**tile-gen**: 500 GB SDD and at least 64 GB ram

**Ubuntu 22** or newer

---

### Warning

This project is made to run on **clean servers** or virtual machines dedicated for this project. The scripts need sudo permissions as they mount/unmount disk images. Do not run this on your dev machine without using virtual machines. If you do, please make sure you understand exactly what each script is doing.

If you run it on a non-clean server, please understand that this will modify your nginx config!

---

## Instructions

#### 1. DNS setup

Set up a server with at least 300 GB SSD space and configure the DNS for the subdomain of your choice.
For example "maps.example.com" -> 185.199.110.153

#### 2. Clone and prepare `config` folder

```
git clone https://github.com/hyperknot/openfreemap
```

In the config folder, copy `.env.sample` to `.env` and set the values.

`DOMAIN_LE` - Your subdomain \
`LE_EMAIL` - Your email for Let's Encrypt

It's recommended to set `SKIP_PLANET=true` first, check if everything works, and run `./init-server.py` a second time with `SKIP_PLANET=false`. This way you get a quick feedback loop for setting up your system.

#### 3. Set up Python if you don't have it yet

On Ubuntu you can get it by `sudo apt install python3-pip`

On macOS you can do `brew install python`

#### 4. Deploy http-host

You run the deploy script locally, and it deploys to a remove server over SSH. You can use a virtualenv if you are used to working with them, but it's not necessary.

```
cd openfreemap
pip install -e .
```

Then run the actual deploy command

```
./init-server.py http-host-static HOSTNAME
```

If you used `SKIP_PLANET=true` then wait a few minutes and see what happens.

If you use `SKIP_PLANET=false` then go for a walk and by the time you come back it should be up and running with the latest planet tiles deployed. Don't worry about the "Download aborted" lines in the meanwhile, it's a bug in CloudFlare.

*// Note: If your server doesn't have an SSD, the download + uncompressing process can take hours.*

---

#### Deploy tile-gen server (optional)

If you have a really beefy machine (see above) and you really want to generate tiles yourself, you can run `./init-server.py tile-gen HOSTNAME`.

Trigger a run manually, by running

```
sudo /data/ofm/venv/bin/python -u /data/ofm/tile_gen/bin/tile_gen.py make-tiles planet
```

It's recommended to use tmux or similar, as it can take days to complete.
