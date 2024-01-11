#!/usr/bin/env python

import marko


def generate():
    licenses = open('../LICENSE.md').read().split('---')[0]
    map_html = open('map.html').read()

    text_md = open('text.md').read()
    text_md = text_md.replace('{licenses}', licenses)

    text_html = marko.convert(text_md)

    template = open('template.html').read()
    template = template.replace('{text}', text_html)
    template = template.replace('{map}', map_html)

    open('index.html', 'w').write(template)


if __name__ == '__main__':
    generate()
