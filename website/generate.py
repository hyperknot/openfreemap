#!/usr/bin/env python
import json
import shutil
from pathlib import Path

import marko


OUT_DIR = Path('_out')
ASSETS_DIR = Path('assets')


def generate():
    shutil.rmtree(OUT_DIR, ignore_errors=True)
    OUT_DIR.mkdir()

    make_index_html()
    make_howto_use()
    make_js()

    make_static_page('privacy', 'Privacy Policy')
    make_static_page('tos', 'Terms of Services')

    copy_assets()


def make_index_html():
    template = open('template_index.html').read()

    main_md = open('blocks/index.md').read()
    main_html = marko.convert(main_md)

    template = template.replace('{body}', main_html)

    map_howto = open('blocks/map.html').read()
    template = template.replace('<!--map_howto-->', map_howto)

    support_plans = open('blocks/support_plans.html').read()
    template = template.replace('<!--support_plans-->', support_plans)

    open(OUT_DIR / 'index.html', 'w').write(template)


def make_howto_use():
    template = open('template_howto_use.html').read()

    map_howto = open('blocks/map.html').read()
    template = template.replace('<!--map_howto-->', map_howto)

    open(OUT_DIR / 'howto_use.html', 'w').write(template)


def make_js():
    pricing_json = json.load(open('assets/pricing.json'))
    support_plans_js = open('assets/support_plans.js').read()
    support_plans_js = support_plans_js.replace(
        "'__PRICING_JSON__'", json.dumps(pricing_json, ensure_ascii=False)
    )
    open(OUT_DIR / 'support_plans.js', 'w').write(support_plans_js)


def copy_assets():
    for file in [
        'style.css',
        'map_howto.js',
        'logo.jpg',
        'favicon.ico',
        'github.svg',
        'x.svg',
        'berlin.webp',
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
