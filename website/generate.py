#!/usr/bin/env python
import shutil
from pathlib import Path

import marko


OUT_DIR = Path('_out')
ASSETS_DIR = Path('assets')


def generate():
    shutil.rmtree(OUT_DIR, ignore_errors=True)
    OUT_DIR.mkdir()

    template = open('template.html').read()

    main_md = open('blocks/main.md').read()
    main_html = marko.convert(main_md)

    index_html = template.replace('{main}', main_html)

    map_docs = open('blocks/map_docs.html').read()
    index_html = index_html.replace('<!--map_docs-->', map_docs)

    support_plans = open('blocks/support_plans.html').read()
    index_html = index_html.replace('<!--support_plans-->', support_plans)

    open(OUT_DIR / 'index.html', 'w').write(index_html)

    make_static_page('privacy', 'Privacy Policy')
    make_static_page('tos', 'Terms of Services')
    copy_assets()


def copy_assets():
    for file in [
        'style.css',
        'logo.jpg',
        'map_docs.js',
        'support_plans.js',
        'favicon.ico',
        'github.svg',
        'x.svg',
    ]:
        shutil.copyfile(ASSETS_DIR / file, OUT_DIR / file)


def make_static_page(page_str, title):
    page_md = open(f'blocks/{page_str}.md').read()
    page_html = marko.convert(page_md)

    template = open('template_static.html').read()
    template = template.replace('{main}', page_html)
    template = template.replace('{title}', title)

    with open(OUT_DIR / f'{page_str}.html', 'w') as fp:
        fp.write(template)


if __name__ == '__main__':
    generate()
