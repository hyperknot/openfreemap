## Is commercial usage allowed?

Yes

## Who is behind this project and how can I follow it?

I'm Zsolt Ero ([X](https://x.com/hyperknot), [blog](https://blog.hyperknot.com/), [email](mailto:zsolt@openfreemap.org)). I built [MapHub](https://maphub.net/) and have been running map hosting in production for 8 years.

X: [hyperknot](https://x.com/hyperknot) and [OpenFreeMapOrg](https://x.com/OpenFreeMapOrg)

GitHub: [openfreemap](https://github.com/hyperknot/openfreemap) and [openfreemap-styles](https://github.com/hyperknot/openfreemap-styles)

## Why did you build this project?

OpenStreetMap is one of the most important collective projects in history. It began 20 years ago, and today, 3 million edits are made each day!

Unfortunately, when you want to use the map on your website or app, you need to look for a commercial map tile provider and hope your site doesn't become too popular. Otherwise, you might end up with a $10,000 bill in a single day, as Hoodmaps [did](https://x.com/levelsio/status/1730659933232730443).

You can try self-hosting, but it requires a big server and a lot of time to get it right.

I waited for years for someone to offer this service but realized that no one was going to do it. So, I thought I might use my map hosting experience and build it myself.

I'll share more about the reasons in a future [blog post](https://blog.hyperknot.com/). Feel free to subscribe.

## How can this work? How can a one-person project offer unlimited map hosting for free?

There is no technical reason why map hosting costs as much as it does today. Vector tiles are just static files. It's true that serving hundreds of millions of files is not easy, but at the end of the day, they are just files.

Financially, the plan is to keep renting servers until they cover the bandwidth. I believe it can be self-sustainable if enough people subscribe to the support plans.

If this project helps you save on your map hosting costs, please consider subscribing to a support plan.

## What is the tech stack?

There is no tile server running; only Btrfs partition images with 300 million hard-linked files. This was my idea; I haven't read about anyone else doing this in production, but it works really well. (You can read more about it on [GitHub](https://github.com/hyperknot/openfreemap).)

There is no cloud, just dedicated servers. The HTTPS server is nginx on Ubuntu.

Special thanks go to [Michael Barry](https://github.com/msbarry) for developing [Planetiler](https://github.com/onthegomap/planetiler). It made it possible to generate the tiles in 5 hours instead of 5 weeks. The map schema is [OpenMapTiles](https://github.com/openmaptiles/openmaptiles).

The [styles](https://github.com/hyperknot/openfreemap-styles) are forked and heavily modified.

## Domains

`tiles.openfreemap.org` - Cloudflare proxied

`direct.openfreemap.org` - direct connection, Round-Robin DNS

## Attribution

Attribution is required. If you are using MapLibre, they are automatically added, you have nothing to do.

If you are using alternative clients, or if you are using this in printed media or video, you must add the following attribution:

<a href="https://openfreemap.org" target="_blank">OpenFreeMap</a> <a href="https://www.openmaptiles.org/" target="_blank">&copy; OpenMapTiles</a> Data from <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>

You do not need to display the OpenFreeMap part, but it is nice if you do.

## License

The license of this project is [MIT](https://www.tldrlegal.com/license/mit-license). Map data is from [OpenStreetMap](https://www.openstreetmap.org/copyright). The licenses for included projects are listed in [LICENSE.md](https://github.com/hyperknot/openfreemap/blob/main/LICENSE.md).
