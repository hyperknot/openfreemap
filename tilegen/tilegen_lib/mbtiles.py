import errno
import json
import shutil
import sqlite3
from pathlib import Path


def update_mbtiles_metadata(mbtiles_path: Path) -> None:
    with sqlite3.connect(mbtiles_path) as conn:
        metadata = dict(conn.execute('select name, value from metadata'))

        conn.execute("update metadata set value='OpenFreeMap' where name='name'")
        conn.execute("update metadata set value='https://openfreemap.org' where name='description'")

        if 'openfreemap' not in metadata['attribution']:
            attribution = (
                '<a href="https://openfreemap.org" target="_blank">OpenFreeMap</a> '
                + metadata['attribution']
            )
            conn.execute("update metadata set value = ? where name = 'attribution'", (attribution,))

        if 'osm_date' not in metadata and 'planetiler:osm:osmosisreplicationtime' in metadata:
            conn.execute(
                'insert into metadata (name, value) values (?, ?)',
                ('osm_date', metadata['planetiler:osm:osmosisreplicationtime'][:10]),
            )


def extract_mbtiles(mbtiles_path: Path, dir_path: Path) -> None:
    """Extract an MBTiles sqlite DB to a folder, hard-linking duplicate tiles."""
    if dir_path.exists() and any(dir_path.iterdir()):
        raise ValueError(f'extract dir is not empty: {dir_path}')

    dir_path.mkdir(exist_ok=True)

    with sqlite3.connect(mbtiles_path) as conn:
        write_dedupl_files(conn, dir_path)
        write_tile_files(conn, dir_path)
        metadata = dict(conn.execute('select name, value from metadata'))

    with (dir_path / 'metadata.json').open('w') as fp:
        json.dump(metadata, fp, indent=2)

    with (dir_path / 'osm_date').open('w') as fp:
        fp.write(metadata['osm_date'])

    print('extract_mbtiles DONE')


def write_dedupl_files(conn: sqlite3.Connection, dir_path: Path) -> None:
    total = conn.execute('select count(*) from tiles_data').fetchone()[0]

    for i, (dedupl_id, tile_data) in enumerate(
        conn.execute('select tile_data_id, tile_data from tiles_data'), start=1
    ):
        dedupl_path = dir_path / 'dedupl' / dedupl_helper_path(dedupl_id)
        dedupl_path.parent.mkdir(parents=True, exist_ok=True)
        with dedupl_path.open('wb') as fp:
            fp.write(tile_data)
        print(f'written dedupl file {i}/{total}')


def write_tile_files(conn: sqlite3.Connection, dir_path: Path) -> None:
    total = conn.execute('select count(*) from tiles_shallow').fetchone()[0]
    extra_dedupl_copies: dict[Path, int] = {}

    for i, (z, x, mbtiles_y, dedupl_id) in enumerate(
        conn.execute('select zoom_level, tile_column, tile_row, tile_data_id from tiles_shallow'),
        start=1,
    ):
        dedupl_path = dir_path / 'dedupl' / dedupl_helper_path(dedupl_id)
        tile_path = dir_path / 'tiles' / str(z) / str(x) / f'{flip_y(z, mbtiles_y)}.pbf'
        tile_path.parent.mkdir(parents=True, exist_ok=True)

        if tile_path.is_file():
            continue

        try:
            link_tile(tile_path, dedupl_path, extra_dedupl_copies)
        except OSError as e:
            if e.errno != errno.EMLINK:
                raise
            extra_dedupl_copies[dedupl_path] = extra_dedupl_copies.get(dedupl_path, 0) + 1
            shutil.copyfile(dedupl_path, dedupl_copy_path(dedupl_path, extra_dedupl_copies))
            print(
                f'Created fixed dedupl file: {dedupl_copy_path(dedupl_path, extra_dedupl_copies)}'
            )
            link_tile(tile_path, dedupl_path, extra_dedupl_copies)

        print(f'hard link created {i}/{total} {i / total * 100:.1f}%: {tile_path}')


def link_tile(tile_path: Path, dedupl_path: Path, extra_dedupl_copies: dict[Path, int]) -> None:
    tile_path.hardlink_to(dedupl_copy_path(dedupl_path, extra_dedupl_copies))


def dedupl_copy_path(dedupl_path: Path, extra_dedupl_copies: dict[Path, int]) -> Path:
    if dedupl_path not in extra_dedupl_copies:
        return dedupl_path
    return dedupl_path.with_name(f'{dedupl_path.name}-{extra_dedupl_copies[dedupl_path]}')


def dedupl_helper_path(dedupl_id: int) -> Path:
    str_num = f'{dedupl_id:09}'
    return Path(str_num[:3]) / str_num[3:6] / f'{str_num[6:]}.pbf'


def flip_y(zoom: int, y: int) -> int:
    return (2**zoom - 1) - y
