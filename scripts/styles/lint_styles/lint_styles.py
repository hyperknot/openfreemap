#!/usr/bin/env python3
import subprocess
from pathlib import Path

import click


@click.command()
@click.argument(
    'styles_folder',
    type=click.Path(exists=True, file_okay=False, resolve_path=True, path_type=Path),
)
def cli(styles_folder):
    p = subprocess.run(['pnpm', 'bin'], capture_output=True, text=True)
    node_bin_path = Path(p.stdout.strip())
    prettier_config_path = node_bin_path.parent.parent / '.prettierrc.js'

    for style_file in styles_folder.rglob('style.json'):
        print(f'formatting {style_file}')
        subprocess.run(
            [node_bin_path / 'prettier', '--config', prettier_config_path, '--write', style_file]
        )
        p = subprocess.run(
            [
                node_bin_path / 'gl-style-format',
                style_file,
            ],
            capture_output=True,
            text=True,
        )
        with open(style_file, 'w') as fp:
            fp.write(p.stdout)


if __name__ == '__main__':
    cli()
