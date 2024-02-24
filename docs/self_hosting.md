# Self-hosting Howto

_note: For most users, **you don't need to run anything**! The tiles are hosted free of charge, without registration. Read the "How can I use it?" section on https://openfreemap.org_

When self-hosting, there are two tasks you can set up on a server (see details in the repo README).

- **http-host**

- **tile-gen**

note: Tile generation is 100% optional, as we are providing the processed full planet files for public download. It also requires a beefy machine, see below.

### System requirements

##### Disk space

​ **http-host**: 300 GB for hosting a single run

​ **tile-gen**: 500 GB for

##### RAM

​ **http-host**: 4 GB

​ **tile-gen**: 64 GB+ RAM.

##### OS

​ **Ubuntu 22+**

### Limitations

There are two limitations in the current beta version:

- You have to set up Let's Encrypt manually or supply your certs.

- The domain is hard-coded to `tiles.openfreemap.org` - you have to edit this.

---

### Warning

This project is made to run on clean servers or virtual machines dedicated for this project. The scripts need sudo permissions as they mount/unmount disk images. Do not run this on your dev machine without using virtual machines. If you do, please make sure you understand exactly what each script is doing.

---

## Instructions

Create virtualenv using: `source prepare-virtualenv.sh`

It's recommended to use [direnv](https://direnv.net/), to have automatic venv activation.

#### 1. Prepare `config` folder

1. If you are not using SSH keys, copy `.env.sample` to `.env` and set the password.
1. `certs` - The contents of this folder gets uploaded to `/data/nginx/certs`.
1. If you want to run tile generation and upload via rclone, you can copy the `rclone.conf.sample` file as well. For simple self-hosting there is no need for this.

#### 2. Certs and domains

Currently the domain is hard coded to `tiles.openfreemap.org`. Please search & replace this.

The script is made with long expiry CloudFlare origin certificates in mind, which are placed in the `config/certs` folder. For self-hosting you may want to use Let's Encrypt or similar automated tool.

If you know how to make Let's Encrypt work with Round Robin DNS, please comment in the Discussions.

#### 3. Deploy a http-host

You run the deploy script locally. It'll connect to an SSH server, like this

`./init-server.py http-host-once HOSTNAME`

After this, go for a walk and by the time you come back it should be up and running with the latest planet tiles deployed. Don't worry about the "Download aborted" lines in the meanwhile, it's a bug in CloudFlare.

#### 4. Deploy tile-gen server (optional)

If you have a really beefy machine (see above) and you want to generate tiles yourself, you can run `./init-server.py tile-gen HOSTNAME`.

Trigger a run manually, by running `planetiler_{area}.sh`. Recommended to use tmux or similar, as it can take days.

### HTTPS certs

The current HTTPS system is made to use long term Cloudflare origin certificates. The same certificates are uploaded to all the servers. This is only possible because CF certs are valid for 15 years.

Once Load Balancing on CF is working, next step will be to integrate Let's Encrypt. If you know how to do this, please comment in the Discussions.
