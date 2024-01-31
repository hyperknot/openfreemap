<a href="https://openfreemap.org/"><img src="website/assets/logo.jpg" alt="logo" height="200" class="logo" /></a>
# OpenFreeMap

[openfreemap.org](https://openfreemap.org)


## Preface: what this is and what this isn't

*Google has more than 7000 people on the Maps team (and that's a [14 year old](https://www.businessinsider.com/apple-has-7000-fewer-people-working-on-maps-than-google-2012-9) number). Mapbox has raised over $500M in funding rounds. It seems like every open-source map company either goes bankrupt or changes to closed-source model.*

How can this project work?

The only way this project can possibly work is to be super focused about what it is and what it isn't.

#### 1.

OFM chooses **building blocks**, which are currently: [OpenStreetMap](https://www.openstreetmap.org/copyright), [OpenMapTiles](https://github.com/openmaptiles/openmaptiles),  [Planetiler](https://github.com/onthegomap/planetiler) (and soon [tilemaker]()), [MapLibre](https://maplibre.org/) and [Natural Earth](https://www.naturalearthdata.com/).

OFM does not want to be an alternative to any of these projects. If the community decides, we can change a building block if it is deemed production-ready. If issues are opened in the scope of these projects, they will be closed and pointed to the right repos.

#### 2.

OFM is providing **full planet vector tile hosting** for displaying maps on websites or mobile apps.

OFM is not about: 

- search or geocoding

- route calculation, navigation or directions

- static image generation

- raster tile hosting

- satellite image hosting

- elevation lookup

- custom tile or dataset hosting

#### 3.

OFM is not something you can install on your dev machine. The only tool you run locally is `init-server.py`.

OFM is a **deploy script** specifically made to set up clean Ubuntu 22+ dedicated servers or virtual machines. It uses [Fabric](https://www.fabfile.org/) and runs commands over SSH. With a single command it can set up a production-ready OFM server, both for tile hosting and generation.

This repo is also Docker free. If someone wants to make a Docker-based version of this, I'm more than happy to link it here.

#### 4.

OFM does not guarantee **automatic updates** for self-hosters. Only enable the cron job if you keep a close eye on this repo. If you just want a trouble-free self-hosting experience, set up a clean server, run the script once, without enabling the cron job and don't touch that machine.

#### 5.

This repo is not something which has to be **constantly updated**, improved, version-bumped. The dream, the ultimate success of this repo is when there are no commits, yet everything works: the map tiles are automatically generated, HTTP servers are automatically updated and load balancing takes care of failing servers.



## How to run?

`source prepare-virtualenv.sh`

You run the script against an SSH server, like this

`./init-server.py HOSTNAME --help`

There are two tasks:

- `--http-host` - Downloads full planet tiles from the public buckets and serves them over HTTPS. Probably the one you want.
- `--tile-gen` - If you have a beefy machine and you want to generate tiles yourself. Not needed for self-hosting.





### Buckets

...







### Warning

This project is made to run on clean servers or virtual machines dedicated for this project. The scripts need sudo permissions as they mount/unmount disk images. Do not run this on your dev machine without using virtual machines. If you do, please make sure you understand exactly what each script is doing.



## Domains and Cloudflare

The project has two domains: .org and .com. Currently, both are on Cloudflare.

The general public only interacts with the .org domain. It has been designed so that this domain can be migrated away from Cloudflare if needed.

The .com domain hosts the R2 buckets, which are required to be on Cloudflare. This domain will always remain on CF.



## FAQ

### System requirements

Ubuntu 22+

Disk space: about 240 GB for hosting a single run, 500 GB for tile gen.



**What about PMTiles?**

I would have loved to use PMTiles; they are a brilliant idea!

Unfortunately, making range requests in 80 GB files just doesn't work in production. It is fine for files smaller than 500 MB, but it has terrible latency and caching issues for full planet datasets.



## Roadmap

v0.2 - load balancing using Round-Robin DNS. 2+ servers for HTTP host

v0.1 - everything works. 1 server for tile gen, 1 server for HTTP host. <- we are here!





## License

The license of this project is [MIT](https://www.tldrlegal.com/license/mit-license). Map data is from [OpenStreetMap](https://www.openstreetmap.org/copyright). The licenses for included projects are listed in [LICENSE.md](https://github.com/hyperknot/openfreemap/blob/main/LICENSE.md).





