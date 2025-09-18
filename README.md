<a href="https://openfreemap.org/"><img src="https://openfreemap.org/logo.jpg" alt="logo" height="200" class="logo" /></a>

# OpenFreeMap

OpenFreeMap lets you display custom maps on your website and apps for free.

You can either [self-host](docs/self_hosting.md) or use our public instance. Everything is **open-source**, including the full production setup — there’s no 'open-core' model here. The map data comes from OpenStreetMap.

Using our **public instance** is completely free: there are no limits on the number of map views or requests. There’s no registration, no user database, no API keys, and no cookies. We aim to cover the running costs of our public instance through donations.

We also provide **weekly** full planet downloads both in Btrfs and MBTiles formats.

#### Quick introduction and how to guide: [https://openfreemap.org/](https://openfreemap.org/)

## Goals of this project

The goal of this project is to provide free, production-quality vector-tile hosting using existing tools.

Currently these tools are: [OpenStreetMap](https://www.openstreetmap.org/copyright), [OpenMapTiles](https://github.com/openmaptiles/openmaptiles), [Planetiler](https://github.com/onthegomap/planetiler), [MapLibre](https://maplibre.org/), [Natural Earth](https://www.naturalearthdata.com/) and [Wikidata](https://www.wikidata.org/wiki/Wikidata:Main_Page).

Special thanks go to [Michael Barry](https://github.com/msbarry) for developing [Planetiler](https://github.com/onthegomap/planetiler). It made it possible to generate the tiles in 5 hours instead of 5 weeks.

The scope of this repo is limited (see below). Once we figure out the technical details, ideally, there should be few commits here, while everything continues to work: the map tiles are automatically generated, servers are automatically updated and load balancing takes care of any downtime.

The [styles repo](https://github.com/hyperknot/openfreemap-styles), on the other hand, is continuously being developed.

Contributions are more than welcome!

## Status of this project

- The tile generation works
- The web servers work
- Weekly auto-updates work
- Servers in our public instance are currently:
  - 1 server running tile generation
  - 2 servers running web hosting
- Web servers are in Round-Robin DNS configuration with Let's Encrypt provided certificates.
- Load-balancer script works. Currently in monitoring-only mode, as Round-Robin DNS handles downtime.
- The public instance has been the production basemap service of [MapHub](https://maphub.net/) since June 2024.

## Sponsoring

Please consider sponsoring our project on [GitHub Sponsors](https://github.com/sponsors/hyperknot).

## Limitations of this project

The only way this project can possibly work is to be super focused about what it is and what it isn't. OpenFreeMap has the following limitations by design:

1. OpenFreeMap is not providing:
   - search or geocoding
   - route calculation, navigation or directions
   - static image generation
   - raster tile hosting
   - satellite image hosting
   - elevation lookup
   - custom tile or dataset hosting

2. OpenFreeMap is not something you can install locally. This repo is a deploy script specifically made to set up clean Ubuntu servers or virtual machines. It uses [Fabric](https://www.fabfile.org/) and runs commands over SSH. With a single command it can set up a production-ready server, both for tile hosting and generation.

   This repo is Docker-free on purpose. If someone wants to make a Docker-based version of this, I'm more than happy to link it here.

3. OpenFreeMap does not promise worry-free automatic updates for self-hosters. Only use the autoupdate version of http-host if you keep a close eye on this repo.

## Self hosting

See [self hosting docs](docs/self_hosting.md).

## What is the tech stack?

There is no tile server running; only Btrfs partition images with 300 million hard-linked files. This was my idea; I haven't read about anyone else doing this in production, but it works really well.

There is no cloud, just dedicated servers. The web server is nginx on Ubuntu.

## Btrfs images

Production-quality hosting of 300 million tiny files is hard. The average file size is just 450 byte. Dozens of tile servers have been written to tackle this problem, but they all have their limitations.

The original idea of this project is to avoid using tile servers altogether. Instead, the tiles are directly served from Btrfs partition images + hard links using an optimised nginx config. I wrote [extract_mbtiles](modules/tile_gen/scripts/extract_mbtiles.py) and [shrink_btrfs](modules/tile_gen/scripts/shrink_btrfs.py) scripts for this very purpose.

This replaces a running service with a pure, file-system-level implementation. Since the Linux kernel's file caching is among the highest-performing and most thoroughly tested codes ever written, it delivers serious performance.

I run some [benchmarks](docs/benchmark/README.md) on a Hetzner server, the aim was to saturate a gigabit connection. At the end, it was able to serve 30 Gbit on loopback interface, on cold nginx cache.

## Code structure

The project has the following parts

#### deploy server - ssh_lib and init-server.py

This sets up everything on a clean Ubuntu server. You run it locally and it sets up the server via SSH.

#### HTTP host - modules/http_host

Inside `http_host`, all work is done by `http_host.py`.

It does the following:

- Downloading btrfs images

- Downloading assets

- Mounting downloaded btrfs images

- Fetches version files

- Running the sync cron task (called every minute with http-host-autoupdate)

You can run `./http_host.py --help` to see which options are available.

#### tile generation - modules/tile_gen

_note: Tile generation is 100% optional, as we are providing the processed full planet btrfs files for public download. You can download full planet images updated weekly, both in Btrfs and in MBTiles format._

The `tile_gen` script downloads a full planet OSM extract and runs it through Planetiler.

The created .mbtiles file is then extracted into a Btrfs partition image using the custom [extract_mbtiles](modules/tile_gen/scripts/extract_mbtiles.py) script. The partition is shrunk using the [shrink_btrfs](modules/tile_gen/scripts/shrink_btrfs.py) script.

Finally, it's uploaded to a public Cloudflare R2 bucket using rclone.

#### styles - [styles repo](https://github.com/hyperknot/openfreemap-styles)

The default styles. I've already put countless hours into tweaking up some nice looking styles. Still, it'll take probably the most work in the long term future.

Of course, you are welcome to use custom styles.

#### load balancer script - modules/loadbalancer

A Round Robin DNS based load balancer script for health checking and updating records. It pushes status messages to a Telegram bot.

## FAQ

### Full planet downloads

Full planet runs are uploaded weekly. You can download them both in Btrfs and in MBTiles formats. The files have the following URL patterns:

https://btrfs.openfreemap.com/areas/planet/{version}/tiles.btrfs.gz (and .mbtiles)

Use the [index file](https://btrfs.openfreemap.com/files.txt) to find out about versions.

_Note: MBTiles files are not required for this project. We provide them for your convenience, allowing you to use the processed planet tiles with any other tool of your choice._

### Public buckets

There are two public buckets:

- https://assets.openfreemap.com - contains fonts, sprites, styles, versions. index: [dirs](https://assets.openfreemap.com/dirs.txt), [files](https://assets.openfreemap.com/files.txt)
- https://btrfs.openfreemap.com - full planet runs. index: [dirs](https://btrfs.openfreemap.com/dirs.txt), [files](https://btrfs.openfreemap.com/files.txt)

### Domains

.org - not hosted through CloudFlare \
.com - hosted through CloudFlare - serving the public buckets

### What about PMTiles and using the Cloud?

I would have loved to use PMTiles; they are a brilliant idea for serverless map hosting!

Unfortunately, on Cloudflare, range requests in 90 GB files have terrible latency, and on AWS, the data transfer costs can be prohibitive.

Of course, with normal usage, you might fall within cloud vendor's free tier, but the internet is full of stories about people receiving surprise bills from AWS, sometimes amounting to thousands of dollars. It only takes one bad crawling bot getting stuck in a loop on your website to trigger such a bill.

In short, using cloud vendors would make it impossible for me to offer this service for free — this project simply wouldn't exist.

## Contributing

Contributors welcome!

Smaller tasks:

- Cloudflare worker for indexing the public buckets, instead of generating index files.
- [styles] Some of the POI icons are missing.

Bigger tasks:

- [styles] Split the styles to building blocks. For example, there should be a POI block, a label block, a road-style related block.

Future:

- Migrate to [Shortbread schema](https://shortbread-tiles.org/) and possibly [VersaTiles](https://versatiles.org/)

#### Dev setup

See [dev setup docs](docs/dev_setup.md).

## Changelog

##### v0.9

Updated Planetiler version to latest
Updated OpenJDK to 24 via Temurin repo

##### v0.8

Lot of self-hosting related fixes.

Generating the domain inside the style TileJSON files dynamically (using nginx sub_filter).

Added SELF_SIGNED_CERTS variable for cases when the certificates are self-managed or self-signed is OK.

##### v0.7

MBTiles are now uploaded, next to the btrfs image files.

##### v0.6

Load-balancer implemented with new config format. Implemented relaxed mode for checking while deployments are happening.

##### v0.5

Using a "done" file in the R2 buckets to mark the upload as finished. All scripts are checking for this file now.

Monaco is generated daily, to avoid too frequent nginx reloads, which might be bad for the in-memory cache.

##### v0.4

Auto-update works!

Monaco is generated hourly. Set-latest runs every minute.

Planet is generated weekly, every Wednesday. Set-latest runs every Saturday.

##### v0.3

Lot of performance related problems with Cloudflare when using Round-Robin DNS. Works much better without any Cloudflare proxying, the browsers actually do a great job of client-side failover and selecting the best host.

Load-balancing script running in check mode again.

##### v0.2

Load-balancing script is running in write mode, updating records when needed.

##### v0.1

Everything works. 1 server for tile gen, 2 servers for HTTP host. Load-balancing script is running in a read-only mode.

## Attribution

Attribution is required. If you are using MapLibre, they are automatically added, you have nothing to do.

If you are using alternative clients, or if you are using this in printed media or video, you must add the following attribution:

<a href="https://openfreemap.org" target="_blank">OpenFreeMap</a> <a href="https://www.openmaptiles.org/" target="_blank">&copy; OpenMapTiles</a> Data from <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>

You do not need to display the OpenFreeMap part, but it is nice if you do.

## License

The license of this project is [MIT](https://www.tldrlegal.com/license/mit-license). Map data is from [OpenStreetMap](https://www.openstreetmap.org/copyright). The licenses for included projects are listed in [LICENSE.md](https://github.com/hyperknot/openfreemap/blob/main/LICENSE.md).
