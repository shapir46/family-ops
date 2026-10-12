"""Find and download freely licensed pictures for the newspaper (Jacob, 2026-10-12). README: "Photo sources".

  python photos.py openverse "red panda"        list photos from Openverse (CC0, public domain, CC BY, BY-SA, BY-NC, BY-NC-SA)
  python photos.py nga "autumn landscape"       list open-access artworks from the National Gallery of Art (CC0)
  python photos.py get openverse <id> out.jpg   download one, then print {"img", "credit", "log"} for edition.json
  python photos.py get nga <uuid> out.jpg

Search results already used in an edition (their "log" tag appears in logs/content-log.md) are skipped.
NGA: nga.gov itself blocks scripts, so this reads NGA's open data on GitHub (about 170 MB, streamed once per
container into a small index in cache/) and fetches images from NGA's IIIF image server.
"""
import csv
import gzip
import io
import json
import os
import re
import sys
from pathlib import Path

import requests

REPO = Path(os.environ.get('REPO') or Path(__file__).resolve().parent.parent)   # run the repo's copy: $REPO/scoop/photos.py
if not (REPO / 'logs/content-log.md').exists():
    raise SystemExit(f'photos.py: no logs/content-log.md under {REPO}; run $REPO/scoop/photos.py or set REPO')
LOG = REPO / 'logs/content-log.md'
CACHE = REPO / 'cache/nga-index.json.gz'
UA = {'User-Agent': 'family-ops (Fairfax Daily Scoop, a private family newspaper)'}
OPENVERSE = 'https://api.openverse.org/v1/images/'
OV_LICENSES = 'cc0,pdm,by,by-sa,by-nc,by-nc-sa'   # no ND: the page crops photos to fit
NGA_DATA = 'https://raw.githubusercontent.com/NationalGalleryOfArt/opendata/main/data/{}.csv'
LICENSE_NAMES = {'cc0': 'CC0', 'pdm': 'public domain'}


def used() -> str:
    return LOG.read_text() if LOG.exists() else ''


def _csv_rows(name):
    r = requests.get(NGA_DATA.format(name), headers=UA, stream=True, timeout=120)
    r.raise_for_status()
    r.encoding = 'utf-8'
    csv.field_size_limit(1 << 30)
    return csv.DictReader(r.iter_lines(decode_unicode=True))


def nga_index():
    """[{uuid, title, date, artist, kind, medium, desc, w, h}] for every open-access primary image."""
    if CACHE.exists():
        return json.loads(gzip.decompress(CACHE.read_bytes()))
    imgs = {}
    for r in _csv_rows('published_images'):
        if r.get('openaccess') == '1' and r.get('viewtype') == 'primary' and r.get('depictstmsobjectid'):
            imgs[r['depictstmsobjectid']] = (r['uuid'], r.get('assistivetext') or '', r.get('width'), r.get('height'))
    out = []
    for r in _csv_rows('objects'):
        im = imgs.get(r.get('objectid'))
        if im:
            out.append({'uuid': im[0], 'title': r.get('title') or '', 'date': r.get('displaydate') or '',
                        'artist': r.get('attribution') or '', 'kind': (r.get('classification') or '').lower(),
                        'medium': r.get('medium') or '', 'desc': im[1][:400], 'w': im[2], 'h': im[3]})
    CACHE.parent.mkdir(exist_ok=True)
    CACHE.write_bytes(gzip.compress(json.dumps(out).encode()))
    return out


def search_openverse(q, n=8):
    # anonymous use: at most 20 results per request
    r = requests.get(OPENVERSE, params={'q': q, 'license': OV_LICENSES, 'category': 'photograph',
                                        'page_size': 20}, headers=UA, timeout=30)
    r.raise_for_status()
    log = used()
    return [x for x in r.json()['results'] if f"openverse:{x['id']}" not in log][:n]


def search_nga(q, n=8, kind=None):
    words = [w for w in re.findall(r'\w+', q.lower()) if len(w) > 2]
    log = used()
    scored = []
    for a in nga_index():
        if (kind and kind not in a['kind']) or f"nga:{a['uuid']}" in log:
            continue
        title, rest = a['title'].lower(), f"{a['desc']} {a['kind']} {a['medium']}".lower()
        s = sum(3 * (w in title) + (w in rest) for w in words)
        if s and all(w in title or w in rest for w in words):
            scored.append((s, a))
    return [a for _, a in sorted(scored, key=lambda t: -t[0])][:n]


def credit_openverse(x):
    lic = LICENSE_NAMES.get(x['license'], f"CC {x['license'].upper()} {x.get('license_version') or ''}".strip())
    src = (x.get('provider') or x.get('source') or '').replace('_', ' ').title()
    return f"{x.get('creator') or 'unknown'} / {src}, {lic}"   # the page adds "Photo:"


def credit_nga(a):
    date = f", {a['date']}" if a['date'] else ''
    return f"{a['artist']}, <i>{a['title']}</i>{date}. National Gallery of Art, Washington (open access)"


def download(url, out):
    r = requests.get(url, headers=UA, timeout=60)
    r.raise_for_status()
    if not r.headers.get('content-type', '').startswith('image/'):
        raise SystemExit(f'not an image: {r.headers.get("content-type")}')
    Path(out).write_bytes(r.content)


def get(src, ident, out):
    if src == 'openverse':
        x = requests.get(f'{OPENVERSE}{ident}/', headers=UA, timeout=30)
        x.raise_for_status()
        x = x.json()
        download(x['url'], out)
        return {'img': str(out), 'credit': credit_openverse(x), 'log': f'openverse:{ident}'}
    a = next(a for a in nga_index() if a['uuid'] == ident)
    download(f'https://api.nga.gov/iiif/{ident}/full/!1200,1200/0/default.jpg', out)
    return {'img': str(out), 'credit': credit_nga(a), 'log': f'nga:{ident}'}


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == 'openverse':
        for x in search_openverse(' '.join(a[1:])):
            print(f"{x['id']}  {x['width']}x{x['height']}  {credit_openverse(x)}  | {x.get('title') or ''}")
    elif len(a) >= 2 and a[0] == 'nga':
        kind = next((k.split('=', 1)[1] for k in a if k.startswith('--kind=')), None)
        for x in search_nga(' '.join(w for w in a[1:] if not w.startswith('--')), kind=kind):
            print(f"{x['uuid']}  {x['kind']}  {x['w']}x{x['h']}  {credit_nga(x)}  | {x['desc'][:120]}")
    elif len(a) == 4 and a[0] == 'get':
        print(json.dumps(get(a[1], a[2], a[3]), ensure_ascii=False))
    else:
        print(__doc__)
