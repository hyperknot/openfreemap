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

    template = open('template.html').read()

    main_md = open('blocks/main.md').read()
    main_html = marko.convert(main_md)

    index_html = template.replace('{main}', main_html)

    map_howto = open('blocks/map_howto.html').read()
    index_html = index_html.replace('<!--map_howto-->', map_howto)

    support_plans = open('blocks/support_plans.html').read()
    index_html = index_html.replace('<!--support_plans-->', support_plans)

    open(OUT_DIR / 'index.html', 'w').write(index_html)

    pricing_json = json.load(open('assets/pricing.json'))
    support_plans_js = open('assets/support_plans.js').read()
    support_plans_js = support_plans_js.replace(
        "'__PRICING_JSON__'", json.dumps(pricing_json, ensure_ascii=False)
    )
    open(OUT_DIR / 'support_plans.js', 'w').write(support_plans_js)

    make_static_page('privacy', 'Privacy Policy')
    make_static_page('tos', 'Terms of Services')
    copy_assets()


def copy_assets():
    for file in [
        'style.css',
        'map_howto.js',
        'logo.jpg',
        'favicon.ico',
        'github.svg',
        'x.svg',
        'mapbg.jpg',
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
