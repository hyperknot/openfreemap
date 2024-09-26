## Is commercial usage allowed?

Yes.

## Do you offer support and SLA guarantees?

At the moment, I don't offer SLA guarantees or personalized support. However, if there's enough interest, I may introduce a Pro plan in the future. If you're interested, please let me know by sending an [email](mailto:zsolt@openfreemap.org).

## What is the tech stack?

There is no tile server running; only nginx serving a Btrfs image with 300 million hard-linked files. This was my idea; I haven't read about anyone else doing this in production, but it works really well. (You can read more about it on [GitHub](https://github.com/hyperknot/openfreemap).)

There is no cloud, just dedicated servers.

Special thanks go to [Michael Barry](https://github.com/msbarry) for developing [Planetiler](https://github.com/onthegomap/planetiler). It made it possible to generate the tiles in 5 hours instead of 5 weeks.

The [styles](https://github.com/hyperknot/openfreemap-styles) are forked and heavily modified. The map schema is unmodified [OpenMapTiles](https://github.com/openmaptiles/openmaptiles).

## Attribution

Attribution is required. If you are using MapLibre, they are automatically added, you have nothing to do.

If you are using alternative clients, or if you are using this in printed media or video, you must add the following attribution:

<a href="https://openfreemap.org" target="_blank">OpenFreeMap</a> <a href="https://www.openmaptiles.org/" target="_blank">&copy; OpenMapTiles</a> Data from <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>

You do not need to display the OpenFreeMap part, but it is nice if you do.

## License

The license of this project is [MIT](https://www.tldrlegal.com/license/mit-license). Map data is from [OpenStreetMap](https://www.openstreetmap.org/copyright). The licenses for included projects are listed in [LICENSE.md](https://github.com/hyperknot/openfreemap/blob/main/LICENSE.md).
