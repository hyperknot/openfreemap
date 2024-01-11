#!/usr/bin/env python

import marko


def generate():
    licenses = open('../LICENSE.md').read().split('---')[0]

    text_md = open('text.md').read()
    text_md = text_md.replace('{licenses}', licenses)

    text_html = marko.convert(text_md)

    template = open('template.html').read()
    template = template.replace('{text}', text_html)

    style_selector = open('map_docs.html').read()
    template = template.replace('<!--map_docs-->', style_selector)

    open('index.html', 'w').write(template)


if __name__ == '__main__':
    generate()
