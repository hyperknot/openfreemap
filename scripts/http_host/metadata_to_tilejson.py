#!/usr/bin/env python3
import json
from pathlib import Path

import click


@click.command()
@click.argument(
    'metadata_path', type=click.Path(exists=True, dir_okay=False, file_okay=True, path_type=Path)
)
@click.argument('tilejson_path', type=click.Path(path_type=Path))
@click.argument('url_prefix')
@click.option('--minify', is_flag=True, help='Minify the generated JSON')
def cli(metadata_path: Path, tilejson_path: Path, url_prefix: str, minify: bool):
    """
    Takes a MBTiles metadata.json and generates a TileJSON 3.0.0 file

    URL_PREFIX: Base URL to use as a prefix for tiles in the generated TileJSON.

    Reference: https://github.com/mapbox/tilejson-spec/tree/master/3.0.0
    """

    tilejson = dict(tilejson='3.0.0')

    with open(metadata_path) as fp:
        metadata = json.load(fp)

    metadata_json_key = json.loads(metadata.pop('json'))

    tilejson['tiles'] = [url_prefix.rstrip('/') + '/{z}/{x}/{y}.pbf']

    ''
    tilejson['vector_layers'] = metadata_json_key.pop('vector_layers')
    assert not metadata_json_key  # check that no more keys are left

    tilejson['attribution'] = metadata.pop('attribution')

    # overwriting new style OSM license, until fixed in tile_gen
    tilejson['attribution'] = (
        '<a href="https://openfreemap.org/" target="_blank">OpenFreeMap</a> '
        '<a href="https://www.openmaptiles.org/" target="_blank">&copy; OpenMapTiles</a> '
        'Data from <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>'
    )

    tilejson['bounds'] = [float(n) for n in metadata.pop('bounds').split(',')]
    tilejson['center'] = [float(n) for n in metadata.pop('center').split(',')]
    tilejson['center'][2] = 1

    tilejson['description'] = metadata.pop('description')

    tilejson['maxzoom'] = int(metadata.pop('maxzoom'))
    tilejson['minzoom'] = int(metadata.pop('minzoom'))

    tilejson['name'] = metadata.pop('name')
    tilejson['version'] = metadata.pop('version')

    with open(tilejson_path, 'w') as fp:
        if minify:
            json.dump(tilejson, fp, ensure_ascii=False, separators=(',', ':'))
        else:
            json.dump(tilejson, fp, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    cli()
