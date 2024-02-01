<a href="https://openfreemap.org/"><img src="website/assets/logo.jpg" alt="logo" height="200" class="logo" /></a>

# OpenFreeMap

[openfreemap.org](https://openfreemap.org)

## Preface: what this is and what this isn't

_Google has more than 7000 people on the Maps team (and that's a [14 year old](https://www.businessinsider.com/apple-has-7000-fewer-people-working-on-maps-than-google-2012-9) number). Mapbox has raised over $500M in funding rounds. It seems like every open-source map company either goes bankrupt or changes to closed-source model._

How can this project work?

The only way this project can possibly work is to be super focused about what it is and what it isn't.

#### 1.

OFM is providing **full planet vector tile hosting** for displaying maps on websites or mobile apps.

OFM is not providing:

- search or geocoding

- route calculation, navigation or directions

- static image generation

- raster tile hosting

- satellite image hosting

- elevation lookup

- custom tile or dataset hosting

#### 2.

OFM chooses **building blocks**, which are currently: [OpenStreetMap](https://www.openstreetmap.org/copyright), [OpenMapTiles](https://github.com/openmaptiles/openmaptiles), [Planetiler](https://github.com/onthegomap/planetiler) , [MapLibre](https://maplibre.org/) and [Natural Earth](https://www.naturalearthdata.com/) and soon [tilemaker](https://github.com/systemed/tilemaker).

OFM does not want to be an alternative to any of these projects. If the community decides, we can change a project if it is deemed production-ready. If issues are opened in the scope of these projects on OFM, they will be closed and pointed to the right repos.

#### 3.

OFM is not something you can install on your dev machine. The only tool you run locally is `init-server.py`.

OFM is a **deploy script** specifically made to set up clean Ubuntu servers or virtual machines. It uses [Fabric](https://www.fabfile.org/) and runs commands over SSH. With a single command it can set up a production-ready OFM server, both for tile hosting and generation.

This repo is also Docker free. If someone wants to make a Docker-based version of this, I'm more than happy to link it here.

#### 4.

OFM does not guarantee **automatic updates** for self-hosters. Only enable the cron job if you keep a close eye on this repo. If you just want a trouble-free self-hosting experience, set up a clean server without the cron job and don't touch that machine.

#### 5.

This repo is not something which has to be constantly updated, improved, version-bumped. The dream, the ultimate success of this repo is when there are **no commits, yet everything works**: the map tiles are automatically generated, HTTP servers are automatically updated and load balancing takes care of failing servers.

## Structure

The project has the following parts

#### ssh_lib and init-server.py - deploy server

This sets up everything on a clean Ubuntu server. You run it locally and it sets up the server via SSH. You specify `--tile-gen` and/or `--http-host` at startup.

#### scripts/tile_gen - tile generation

The `tile_gen` scripts download a full planet OSM extract and run it through Planetiler (and soon tilemaker). Currently a run is triggered manually, by running `planetiler_{area}.sh`.

The created .mbtiles file is then extracted into a BTRFS partition image using the custom [extract_mbtiles](scripts/tile_gen/extract_mbtiles) script. The partition is shrunk using the [shrink_btrfs](scripts/tile_gen/shrink_btrfs) script.

Finally, it's uploaded to a public Cloudflare R2 bucket using rclone.

*Note: Perhaps the most original aspect of this repository is the use of partition images and hard links. I experimented with ext4 first, but BTRFS proved to be a better fit for the job, with much smaller resulting images. I wrote extract_mbtiles and shrink_btrfs scripts for this very purpose.*

#### scripts/http_host - HTTP host

Inside `http_host`, all work is done by `host_manager.py`. It checks the most up-to-date files in the public buckets and downloads/extracts them locally, if needed.

It mounts the downloaded BTRFS images in `/mnt/ofm`, creates the correct TileJSON file and updates nginx with the correct config.

You can run `./host_manager.py --help` to see which options are available. Some commands can be run locally, including on non-linux machines.

#### styles, fonts, icons, compare tool - in separate [styles repo](https://github.com/hyperknot/openfreemap-styles)

## How to run?

Use Python 3.10/3.11.

Create virtualenv using: `source prepare-virtualenv.sh`

It's recommended to use [direnv](https://direnv.net/), to have automatic venv activation.

##### 1. Prepare config folder

1. copy the .sample files and change the values

2. SSH_PASSWD is only needed if you don't use SSH keys.

3. rclone.conf is only needed for uploading. For http_host there is no need for this file.

4. certs - these are the certs for nginx. If you put a cert here, it'll be uploaded to `/data/nginx/certs`.

   Currently the nginx config is hard coded to use for `openfreemap.org.cert` and `openfreemap.org.key`.

##### 2. Deploy a HTTP host

You run the deploy script locally, and it'll connect to an SSH server, like this

`./init-server.py HOSTNAME --http-host`

After this, go for a walk and by the time you come back it should be up and running.

When it's finished it's a good idea to delete the cron job with `rm /etc/cron.d/ofm_http_host` , see warning below.

##### 3. Deploy tile gen server (optional)

- If you have a beefy machine and you want to generate tiles yourselfm you can run the same script with `--tile-gen`. Not needed for self-hosting.

#### Warning

This project is made to run on clean servers or virtual machines dedicated for this project. The scripts need sudo permissions as they mount/unmount disk images. Do not run this on your dev machine without using virtual machines. If you do, please make sure you understand exactly what each script is doing.

## Downloads and buckets

There are three public buckets:

- https://assets.openfreemap.com - contains fonts, sprites, styles, versions. index: [dirs](https://assets.openfreemap.com/dirs.txt), [files](https://assets.openfreemap.com/index.txt)
- https://planet.openfreemap.com - full planet runs. index: [dirs](https://planet.openfreemap.com/dirs.txt), [files](https://planet.openfreemap.com/index.txt)
- https://monaco.openfreemap.com - identical runs to the full planet, but only for Monaco area. Very tiny, ideal for development. index: [dirs](https://monaco.openfreemap.com/dirs.txt), [files](https://monaco.openfreemap.com/index.txt)

#### Full planet downloads

You can directly download the processed full planet runs on the following URLs:

https://planet.openfreemap.com/20231221_134737_pt/tiles.mbtiles // 84 GB, mbtiles file
https://planet.openfreemap.com/20231221_134737_pt/tiles.btrfs.gz // 81 GB, BTRFS partition image

Replace the `20231221_134737_pt` part with any newer run, from the [index file](https://planet.openfreemap.com/index.txt).


## HTTPS certs

The current HTTPS system is made to use long term Cloudflare origin certificates. The same certificates are uploaded to all the server. This is only possible because CF certs are valid for 15 years.

Once Load Balancing on CF is working, next step will be to integrate Let's Encrypt. If you know how to do this, please comment in the Discussions.

## Domains and Cloudflare

The project has two domains: .org and .com. Currently, both are on Cloudflare.

The general public only interacts with the .org domain. It has been designed so that this domain can be migrated away from Cloudflare if needed.

The .com domain hosts the R2 buckets, which are required to be on Cloudflare. This domain will always remain on CF.

## FAQ

### System requirements

Ubuntu 22+

Disk space: about 240 GB for hosting a single run, 500 GB for tile gen.

### What about PMTiles?

I would have loved to use PMTiles; they are a brilliant idea!

Unfortunately, making range requests in 80 GB files just doesn't work in production. It is fine for files smaller than 500 MB, but it has terrible latency and caching issues for full planet datasets.

If PMTiles implements splitting to <10 MB files, it can be a valid alternative to running servers.

## Contributors

Contributors welcome!

Smaller tasks:

- Add tilemaker as well, so we see the difference between planetiler and tilemaker and they can both validate their output based on this comparison.
- Figure out Let's Encrypt for Round Robin DNS. I mean we have multiple servers under the same subdomain, how do you handle the certs.
- Cloudflare worker for indexing the public buckets, instead of manually generating index.txt files.
- Some of the POI icons are missing in the styles.

Bigger tasks:

- Split the styles to blocks and build it up from there. For example, there should only be one, reference implementation of all the road layers, and all styles should use this.
- Automate tile-gen, uploading, testing and setting versions. Need

Tasks outside the scope of this project:

- Make a successor for the OpenMapTiles schema. Maptiler went proprietary and the repo is abandoned now. If there is a community supported successor, I'm happy to change.
- 



## Roadmap

v0.1 - everything works. 1 server for tile gen, 1 server for HTTP host. <- we are here!

v0.2 - load balancing using Round-Robin DNS on Cloudflare.

future

- load balancing on Let's Encrypt

- support tilemaker in addition to planetiler
- automatic tile-gen and upload

## License

The license of this project is [MIT](https://www.tldrlegal.com/license/mit-license). Map data is from [OpenStreetMap](https://www.openstreetmap.org/copyright). The licenses for included projects are listed in [LICENSE.md](https://github.com/hyperknot/openfreemap/blob/main/LICENSE.md).
