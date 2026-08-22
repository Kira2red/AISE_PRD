#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成自包含 HTML（内联 style.css + base64 内嵌 logo），用于飞书文档嵌入。
用法：python3 make_standalone.py  （输出到 standalone/ 目录）
"""
import base64, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
WWW = os.path.join(ROOT, 'www')
OUT = os.path.join(ROOT, 'standalone')
os.makedirs(OUT, exist_ok=True)

CSS = open(os.path.join(WWW, 'style.css'), encoding='utf-8').read()

def img_b64(name):
    with open(os.path.join(WWW, name), 'rb') as f:
        return 'data:image/png;base64,' + base64.b64encode(f.read()).decode()

IMAGES = {'aise-logo.png': img_b64('aise-logo.png'),
          'csia-logo.png': img_b64('csia-logo.png')}

pages = ['index.html', 'card.html', 'report.html', 'admin.html']
for name in pages:
    html = open(os.path.join(WWW, name), encoding='utf-8').read()
    # 1. 内联 CSS
    html = html.replace('<link rel="stylesheet" href="style.css">',
                        '<style>\n' + CSS + '\n</style>')
    # 2. 内嵌 logo
    for img, uri in IMAGES.items():
        html = html.replace('src="' + img + '"', 'src="' + uri + '"')
    out = os.path.join(OUT, name)
    open(out, 'w', encoding='utf-8').write(html)
    # 自检：无外部引用残留
    assert 'href="style.css"' not in html, name + ' CSS 未内联'
    assert re.search(r'src="(aise|csia)-logo\.png"', html) is None, name + ' logo 未内联'
    print('✓ %-14s %6.1f KB（自包含）' % (name, os.path.getsize(out) / 1024))

print('\n输出目录:', OUT)
