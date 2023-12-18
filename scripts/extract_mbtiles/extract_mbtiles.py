#!/usr/bin/env python3
import json
import os
import shutil
import sqlite3
import sys
from pathlib import Path

import click


@click.command()
@click.argument(
    'mbtiles_path',
    type=click.Path(exists=True, dir_okay=False, file_okay=True, path_type=Path),
)
@click.argument('dir_path', type=click.Path(dir_okay=True, file_okay=False, path_type=Path))
def cli(mbtiles_path: Path, dir_path: Path):
    """
    Extracts a mbtiles sqlite to a folder
    Deduplicating identical tiles as hard-links

    used for reference: https://github.com/mapbox/mbutil
    """

    if dir_path.exists() and any(dir_path.iterdir()):
        sys.exit('Dir not empty')

    dir_path.mkdir(exist_ok=True)

    conn = sqlite3.connect(mbtiles_path)
    c = conn.cursor()

    write_metadata(c, dir_path=dir_path)
    write_dedupl_files(c, dir_path=dir_path)
    write_tile_files(c, dir_path=dir_path)

    # remove dedupl files at the end
    shutil.rmtree(dir_path / 'dedupl')

    # if it's a full planet run,
    # make sure there are exactly the right number of files generated
    if 'planet' in mbtiles_path.parent.name:
        assert count_files(dir_path / 'tiles') == calculate_tiles_sum(14)


def write_metadata(c, *, dir_path):
    metadata = dict(c.execute('select name, value from metadata').fetchall())
    json.dump(metadata, open(dir_path / 'metadata.json', 'w'), indent=2)


def write_dedupl_files(c, *, dir_path):
    # dedupl files
    # write out the tiles_data files into a multi-level folder
    total = c.execute('select count(*) from tiles_data').fetchone()[0]

    c.execute('select tile_data_id, tile_data from tiles_data')

    for i, row in enumerate(c, start=1):
        dedupl_id = row[0]
        dedupl_path = dir_path / 'dedupl' / dedupl_helper_path(dedupl_id)
        dedupl_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dedupl_path, 'wb') as fp:
            fp.write(row[1])
            print(f'written dedupl file {i}/{total}')


def write_tile_files(c, *, dir_path):
    total = c.execute('select count(*) from tiles_shallow').fetchone()[0]

    bug_fix_dict = {}

    c.execute('select zoom_level, tile_column, tile_row, tile_data_id from tiles_shallow')
    for i, row in enumerate(c, start=1):
        if i < 4678400:
            continue

        z = row[0]
        x = row[1]
        y = flip_y(z, row[2])
        dedupl_id = row[3]

        dedupl_path = dir_path / 'dedupl' / dedupl_helper_path(dedupl_id)
        dedupl_path_fixed = get_fixed_dedupl_name(bug_fix_dict, dedupl_path)

        tile_path = dir_path / 'tiles' / str(z) / str(x) / f'{y}.pbf'
        tile_path.parent.mkdir(parents=True, exist_ok=True)

        if tile_path.is_file():
            continue

        # create the hard link
        try:
            tile_path.hardlink_to(dedupl_path_fixed)
            print(f'hard link created {i}/{total} {i / total * 100:.1f}%: {tile_path}')
        except OSError as e:
            # fixing BTRFS's 64k max link limit
            if e.errno == 31:
                bug_fix_dict.setdefault(dedupl_path, 0)
                bug_fix_dict[dedupl_path] += 1
                dedupl_path_fixed = get_fixed_dedupl_name(bug_fix_dict, dedupl_path)
                shutil.copyfile(dedupl_path, dedupl_path_fixed)
                print(f'Created fixed dedupl file: {dedupl_path_fixed}')
                tile_path.hardlink_to(dedupl_path_fixed)
                print(f'hard link created {i}/{total} {i / total * 100:.1f}%: {tile_path}')
            else:
                raise


def count_files(folder):
    total = 0
    for root, dirs, files in os.walk(folder):
        total += len(files)
    return


def get_fixed_dedupl_name(bug_fix_dict, dedupl_path):
    if dedupl_path in bug_fix_dict:
        return dedupl_path.with_name(f'{dedupl_path.name}-{bug_fix_dict[dedupl_path]}')
    else:
        return dedupl_path


def dedupl_helper_path(dedupl_id: int) -> Path:
    """
    Naming 200 million files such that each subdir has max 1000 children
    """

    str_num = f'{dedupl_id:09}'
    l1 = str_num[:3]
    l2 = str_num[3:6]
    l3 = str_num[6:]
    return Path(l1) / l2 / f'{l3}.pbf'


def flip_y(zoom, y):
    return (2**zoom - 1) - y


def calculate_tiles(zoom_level):
    return (2**zoom_level) ** 2


def calculate_tiles_sum(zoom_level):
    """
    Tiles up to zoom level (geometric series)
    """
    return (4 ** (zoom_level + 1) - 1) // 3


if __name__ == '__main__':
    cli()
