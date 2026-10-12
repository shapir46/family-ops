"""Painted comic backdrops, made with xAI's Grok image API (Jacob, 2026-10-12). README: "Comic: painted backdrops".

A backdrop is scenery only (no characters, no text). It is painted once, reviewed, committed to scoop/backdrops/
and then reused like a drawn scene: edition.json `comic` names it as a panel's `scene` and the original art.py
cast stands on top. The daily run never calls this; the library grows only through /newspaper-design.

  python backdrops.py list
  python backdrops.py make farm "a pumpkin patch farm with hay bales and a red barn far away" --season=fall
  python backdrops.py make rink "an outdoor ice rink in a snowy park" --season=winter --ground=104
  python backdrops.py remove farm

`make` writes backdrops/<name>.jpg and its entry in backdrops/index.json, replacing an earlier one of the same name.
Look at the file before committing (Read it): scenery only, no letters or faces, open ground for the cast.
`--ground` is the panel y (0-122) where the cast's feet go; default 108. Needs XAI_API_KEY (never printed).
XAI_BACKDROP_MODEL picks the model; default grok-imagine-image-2.0.
"""
import io
import json
import os
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIR = HERE / 'backdrops'
INDEX = DIR / 'index.json'
MODEL = 'grok-imagine-image-2.0'
SIZE = (600, 366)                     # 3x the panel viewBox (200 x 122), enough for print at strip width
STYLE = ("Background scenery for one panel of a children's newspaper comic strip. Cheerful picture-book style, "
         "flat bright colors with clean dark ink outlines, soft simple shading, not too busy. Wide landscape view at "
         "eye level. Scenery only: no people, no animals, no creatures, no faces, no characters. No text, letters, "
         "numbers, signs, posters or logos anywhere. The lower middle of the picture is open and uncluttered, with "
         "flat empty ground across the bottom fifth, where cartoon characters will be drawn standing later. Scene: ")
SEASONS = ('any', 'fall', 'winter', 'spring', 'summer')


def load():
    return json.loads(INDEX.read_text()) if INDEX.exists() else {}


def save(idx):
    INDEX.write_text(json.dumps(dict(sorted(idx.items())), indent=1, ensure_ascii=False) + '\n')


def fit(data):
    """Center-crop to the panel's shape and resize; returns JPEG bytes."""
    from PIL import Image
    im = Image.open(io.BytesIO(data)).convert('RGB')
    w, h = im.size
    want = SIZE[0] / SIZE[1]
    if w / h > want:
        cw = round(h * want)
        im = im.crop(((w - cw) // 2, 0, (w - cw) // 2 + cw, h))
    else:
        ch = round(w / want)
        im = im.crop((0, h - ch, w, h))             # taller than needed: keep the ground, trim the sky
    im = im.resize(SIZE, Image.LANCZOS)
    # A light wash so the drawn cast stands out from the scenery (and the printer uses less ink)
    from PIL import ImageEnhance
    im = Image.blend(ImageEnhance.Color(im).enhance(.8), Image.new('RGB', SIZE, 'white'), .18)
    out = io.BytesIO()
    im.save(out, 'JPEG', quality=84, optimize=True)
    return out.getvalue()


def make(name, subject, season='any', ground=108):
    sys.path.insert(0, str(HERE))
    import art
    import illustrate
    if not name.replace('_', '').isalnum() or name != name.lower():
        raise SystemExit('backdrops.py: name must be lowercase letters, digits and _')
    if name in art.SCENES:
        raise SystemExit(f"backdrops.py: '{name}' is already a drawn scene; pick another name")
    if season not in SEASONS:
        raise SystemExit(f'backdrops.py: season must be one of {", ".join(SEASONS)}')
    if not 80 <= ground <= 118:
        raise SystemExit('backdrops.py: --ground must be 80-118 (panel units)')
    model = os.environ.get('XAI_BACKDROP_MODEL', MODEL)
    jpg = fit(illustrate.request_image(STYLE + subject, model, '16:9'))
    DIR.mkdir(exist_ok=True)
    (DIR / f'{name}.jpg').write_bytes(jpg)
    idx = load()
    idx[name] = {'subject': subject, 'season': season, 'ground': ground, 'model': model, 'made': date.today().isoformat()}
    save(idx)
    return {'name': name, 'file': str(DIR / f'{name}.jpg'), 'bytes': len(jpg), **idx[name]}


def remove(name):
    idx = load()
    if name not in idx:
        raise SystemExit(f"backdrops.py: no backdrop '{name}'")
    del idx[name]
    save(idx)
    (DIR / f'{name}.jpg').unlink(missing_ok=True)


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    opt = dict(x[2:].split('=', 1) for x in sys.argv[1:] if x.startswith('--') and '=' in x)
    if a[:1] == ['list']:
        for k, v in load().items():
            print(f"{k:14} {v['season']:7} ground {v['ground']:<4} {v['subject']}")
    elif a[:1] == ['make'] and len(a) == 3:
        print(json.dumps(make(a[1], a[2], opt.get('season', 'any'), int(opt.get('ground', 108))), ensure_ascii=False))
    elif a[:1] == ['remove'] and len(a) == 2:
        remove(a[1])
        print('removed', a[1])
    else:
        raise SystemExit(__doc__)
