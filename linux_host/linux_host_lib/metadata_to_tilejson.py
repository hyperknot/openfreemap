import json
from pathlib import Path
from typing import Any


def write_tilejson(metadata_path: Path, tilejson_path: Path, url_prefix: str) -> None:
    """Convert MBTiles metadata into a minified TileJSON 3.0.0 file."""
    with metadata_path.open() as fp:
        metadata = json.load(fp)

    metadata_json = json.loads(metadata.pop('json'))
    tilejson: dict[str, Any] = {
        'tilejson': '3.0.0',
        'tiles': [url_prefix.rstrip('/') + '/{z}/{x}/{y}.pbf'],
        'vector_layers': metadata_json.pop('vector_layers'),
    }
    assert not metadata_json

    metadata.pop('attribution')
    # Override the new-style OSM license until tilegen supplies the desired attribution.
    tilejson['attribution'] = (
        '<a href="https://openfreemap.org" target="_blank">OpenFreeMap</a> '
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

    with tilejson_path.open('w') as fp:
        json.dump(tilejson, fp, ensure_ascii=False, separators=(',', ':'))
