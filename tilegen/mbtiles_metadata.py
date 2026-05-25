import json
import sqlite3
from pathlib import Path


def update_mbtiles_metadata(mbtiles_path: Path) -> None:
    with sqlite3.connect(mbtiles_path) as conn:
        metadata = dict(conn.execute('select name, value from metadata').fetchall())

        conn.execute("update metadata set value='OpenFreeMap' where name='name'")
        conn.execute("update metadata set value='https://openfreemap.org' where name='description'")

        attribution = metadata.get('attribution', '')
        if 'openfreemap' not in attribution.lower():
            attribution = (
                '<a href="https://openfreemap.org" target="_blank">OpenFreeMap</a> ' + attribution
            )
            conn.execute("update metadata set value = ? where name = 'attribution'", (attribution,))

        if 'osm_date' not in metadata and 'planetiler:osm:osmosisreplicationtime' in metadata:
            osm_date = metadata['planetiler:osm:osmosisreplicationtime'][:10]
            conn.execute('insert into metadata (name, value) values (?, ?)', ('osm_date', osm_date))


def write_metadata_files(mbtiles_path: Path, dir_path: Path) -> None:
    with sqlite3.connect(mbtiles_path) as conn:
        metadata = dict(conn.execute('select name, value from metadata').fetchall())

    with (dir_path / 'metadata.json').open('w') as fp:
        json.dump(metadata, fp, indent=2)

    with (dir_path / 'osm_date').open('w') as fp:
        fp.write(metadata['osm_date'])
