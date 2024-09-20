# Self-hosting Howto

You can either self-host or use our public instance. Everything is **open-source**, including the full production setup — there’s no 'open-core' model here.

When self-hosting, there are two tasks you can set up on a server (see details in the repo README).

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

Create virtualenv using: `source prepare-virtualenv.sh`

It's recommended to use [direnv](https://direnv.net/), to have automatic venv activation.

#### 1. Prepare `config` folder

1. Copy `.env.sample` to `.env` and set the values.

   DOMAIN_LE - Use this to specify a domain to be used with Let's Encrypt.

1. If you want to run tile generation and upload via rclone, you can copy the `rclone.conf.sample` file as well. For simple self-hosting there is no need for this.

#### 2. Deploy a http-host

You run the deploy script locally. It'll connect to an SSH server, like this

`./init-server.py http-host-static HOSTNAME`

After this, go for a walk and by the time you come back it should be up and running with the latest planet tiles deployed. Don't worry about the "Download aborted" lines in the meanwhile, it's a bug in CloudFlare.

#### 3. Deploy tile-gen server (optional)

If you have a really beefy machine (see above) and you want to generate tiles yourself, you can run `./init-server.py tile-gen HOSTNAME`.

Trigger a run manually, by running `planetiler_{area}.sh`. Recommended to use tmux or similar, as it can take days to complete.
