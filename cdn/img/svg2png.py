#!/usr/bin/env python3
"""svg2png: convert SVG to PNG at ~target width.
Tries cairosvg first, falls back to chrome-headless-shell screenshot.
Usage: svg2png.py <src.svg> <dst.png> [width_px]"""
import sys, subprocess, os, re, tempfile, glob

def via_cairosvg(src, dst, width):
    import cairosvg
    cairosvg.svg2png(url=src, write_to=dst, output_width=width)

def via_chrome(src, dst, width):
    cands = (glob.glob(os.path.expanduser('~/.cache/puppeteer/chrome-headless-shell/*/chrome-headless-shell')) +
             glob.glob(os.path.expanduser('~/.cache/puppeteer/chrome/*/chrome')) +
             glob.glob(os.path.expanduser('~/.cache/puppeteer/chrome-headless-shell/*')))
    exe = next((c for c in cands if os.path.isfile(c) and os.access(c, os.X_OK)), None)
    if not exe:
        raise RuntimeError("no chrome-headless-shell binary found")
    svg = open(src, encoding='utf-8').read()
    m = re.search(r'viewBox="([\d.\- ]+)"', svg)
    if m:
        parts = [float(x) for x in m.group(1).split()]
        aspect = parts[3] / parts[2] if parts[2] else 0.75
    else:
        aspect = 0.75
    height = max(200, int(width * aspect) + 40)
    html = ('<!DOCTYPE html><html><head><meta charset="utf-8">'
            '<style>html,body{margin:0;padding:0;background:#fff}'
            'img{display:block;width:%dpx;height:auto}</style></head>'
            '<body><img src="file://%s"></body></html>' % (width, src))
    tmp = tempfile.NamedTemporaryFile('w', suffix='.html', delete=False)
    tmp.write(html); tmp.close()
    try:
        subprocess.run([exe, '--headless', '--no-sandbox', '--disable-gpu',
                        '--hide-scrollbars',
                        '--window-size=%d,%d' % (width, height),
                        '--screenshot=' + dst, 'file://' + tmp.name],
                       check=True, capture_output=True, timeout=90)
    finally:
        os.unlink(tmp.name)

if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 900
    try:
        via_cairosvg(src, dst, width)
        print('OK cairosvg', dst)
    except ImportError as e:
        via_chrome(src, dst, width)
        print('OK chrome-fallback', dst)
