<a href="https://openfreemap.org/"><img src="website/assets/logo.jpg" alt="logo" height="200" class="logo" /></a>

# OpenFreeMap

[openfreemap.org](https://openfreemap.org)

## What is OpenFreeMap?

OpenFreeMap provides free map hosting so you can display custom maps on your website and apps.

It is truly **free**: there are no limits on the number of map views or requests you can make, nor on how you use your map. There is no registration page, user database, API keys, or cookies.

It is truly **open-source**: everything, including the full production setup, is in this repo. Map data is from OpenStreetMap.

## Goals of this project

The goal of this project is to provide free, production-quality vector-tile hosting using existing tools.

Currently these tools are: [OpenStreetMap](https://www.openstreetmap.org/copyright), [OpenMapTiles](https://github.com/openmaptiles/openmaptiles), [Planetiler](https://github.com/onthegomap/planetiler), [MapLibre](https://maplibre.org/), [Natural Earth](https://www.naturalearthdata.com/) and [Wikidata](https://www.wikidata.org/wiki/Wikidata:Main_Page).

Special thanks go to [Michael Barry](https://github.com/msbarry) for developing [Planetiler](https://github.com/onthegomap/planetiler). It made it possible to generate the tiles in 5 hours instead of 5 weeks.

The scope of this repo is limited (see below). Once we figure out the technical details, ideally, there should be few commits here, while everything continues to work: the map tiles are automatically generated, servers are automatically updated and load balancing takes care of any downtime.

The [styles repo](https://github.com/hyperknot/openfreemap-styles), on the other hand, is continuously being developed.

Contributions are more than welcome!

## Limitations of this project

The only way this project can possibly work is to be super focused about what it is and what it isn't. OFM has the following limitations by design:

1. OFM is not providing:

   - search or geocoding
   - route calculation, navigation or directions
   - static image generation
   - raster tile hosting
   - satellite image hosting
   - elevation lookup
   - custom tile or dataset hosting

2. OFM is not something you can install on your dev machine. OFM is a deploy script specifically made to set up clean Ubuntu servers or virtual machines. It uses [Fabric](https://www.fabfile.org/) and runs commands over SSH. With a single command it can set up a production-ready OFM server, both for tile hosting and generation.

   This repo is also Docker free. If someone wants to make a Docker-based version of this, I'm more than happy to link it here.

3. OFM does not promise worry-free automatic updates for self-hosters. Only use the autoupdate version of http-host if you keep a close eye on this repo.

## What is the tech stack?

There is no tile server running; only Btrfs partition images with 300 million hard-linked files. This was my idea; I haven't read about anyone else doing this in production, but it works really well.

There is no cloud, just dedicated servers. The HTTPS server is nginx on Ubuntu.

## Btrfs images

Production-quality hosting of 300 million tiny files is hard. The average file size is just 450 byte. Dozens of tile servers have been written to tackle this problem, but they all have their limitations.

The original idea of this project is to avoid using tile servers altogether. Instead, the tiles are directly served from Btrfs partition images + hard links using an optimised nginx config. I wrote [extract_mbtiles](modules/tile_gen/scripts/extract_mbtiles.py) and [shrink_btrfs](modules/tile_gen/scripts/shrink_btrfs.py) scripts for this very purpose.

This replaces a running service with a pure, file-system-level implementation. Since the Linux kernel's file caching is among the highest-performing and most thoroughly tested codes ever written, it delivers serious performance.

I run some [benchmarks](docs/quick_notes/http_benchmark.md) on a Hetzner server, the aim was to saturate a gigabit connection. At the end, it was able to serve 30 Gbit on loopback interface, on cold nginx cache.

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

_note: Tile generation is 100% optional, as we are providing the processed full planet btrfs files for public download._

The `tile_gen` script downloads a full planet OSM extract and runs it through Planetiler.

The created .mbtiles file is then extracted into a Btrfs partition image using the custom [extract_mbtiles](modules/tile_gen/scripts/extract_mbtiles.py) script. The partition is shrunk using the [shrink_btrfs](modules/tile_gen/scripts/shrink_btrfs.py) script.

Finally, it's uploaded to a public Cloudflare R2 bucket using rclone.

#### styles - [styles repo](https://github.com/hyperknot/openfreemap-styles)

A very important part, probably needs the most work in the long term future.

#### load balancer script - modules/loadbalancer

A Round Robin DNS based load balancer script for health checking and updating records. It pushes status messages to a Telegram bot.

## Self hosting

See [self hosting docs](docs/self_hosting.md).

## FAQ

### Full planet downloads

You can directly download the processed full planet runs on the following URL patterns:

https://planet.openfreemap.com/20240607_232801_pt/tiles.btrfs.gz // 86 GB

Replace the `20240607_232801_pt` part with any newer run, from the [index file](https://planet.openfreemap.com/files.txt).

### Public buckets

There are two public buckets:

- https://assets.openfreemap.com - contains fonts, sprites, styles, versions. index: [dirs](https://assets.openfreemap.com/dirs.txt), [files](https://assets.openfreemap.com/files.txt)
- https://btrfs.openfreemap.com - full planet runs. index: [dirs](https://btrfs.openfreemap.com/dirs.txt), [files](https://btrfs.openfreemap.com/files.txt)

### What about PMTiles?

I would have loved to use PMTiles; they are a brilliant idea!

Unfortunately, making range requests in 80 GB files just doesn't work in production. It is fine for files smaller than 500 MB, but it has terrible latency and caching issues for full planet datasets.

If PMTiles implements splitting to <10 MB files, it can be a valid alternative to running servers.

## Contributing

Contributors welcome!

Smaller tasks:

- Cloudflare worker for indexing the public buckets, instead of generating index files.
- Some of the POI icons are missing in the styles.

Bigger tasks:

- Split the styles to building blocks. For example, there should be a POI block, a label block, a road-style related block.
- Implement automatic updates for tile gen, uploading, testing and setting versions. (work-in-progress as of today)

Tasks outside the scope of this project:

- Make a successor for the OpenMapTiles schema.

#### Dev setup

See [dev setup docs](docs/dev_setup.md).

## Changelog

##### v0.6
Load-balancer implemented with new config format.

##### v0.5

Using a "done" file in the R2 buckets to mark the upload as finished. All scripts are checking for this file now.

Monaco is generated daily, to avoid too frequent nginx reloads, which might be bad for the in-memory cache.

##### v0.4

Auto-update works!

Monaco is generated hourly. set-latest runs every minute.

Planet is generated weekly, every Wednesday. set-latest runs every Saturday.

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
