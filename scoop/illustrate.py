"""AI illustrations for fun pieces in the newspaper, made with xAI's Grok image API (Jacob, 2026-10-12).
README: "AI illustrations". Only for picture extras on fun, non-news pieces; never news, the headline or the critter.

  python illustrate.py "a fox and a polar bear raking a giant leaf pile" out.jpg

Prints {"img", "illus": true, "log"} for an edition.json extra. The house style below is added to every prompt.
Needs XAI_API_KEY in the environment (an environment secret; never printed, logged or committed).
XAI_IMAGE_MODEL picks the model; otherwise the first image model the account offers is used.
On any failure it exits non-zero and the extra simply runs without a picture.
"""
import base64
import hashlib
import json
import os
import sys
from datetime import date
from pathlib import Path

import requests

API = 'https://api.x.ai/v1'
STYLE = ('Cheerful children\'s picture-book illustration, flat bright colors with clean dark outlines, simple light '
         'background, friendly and gentle, suitable for young kids. No text, letters, numbers, signs or logos. '
         'No real or famous people, no recognizable children, no characters from movies, TV, books, games or brands. '
         'Subject: ')


def _key():
    k = os.environ.get('XAI_API_KEY')
    if not k:
        raise SystemExit('illustrate.py: XAI_API_KEY is not set in this environment (environment secret); no illustration')
    return k


def _get(path, key):
    r = requests.get(f'{API}/{path}', headers={'Authorization': f'Bearer {key}'}, timeout=30)
    if r.status_code != 200:
        raise SystemExit(f'illustrate.py: xAI {path} returned HTTP {r.status_code}')
    return r.json()


def model(key):
    if os.environ.get('XAI_IMAGE_MODEL'):
        return os.environ['XAI_IMAGE_MODEL']
    ids = [m.get('id') for m in _get('image-generation-models', key).get('models', []) if m.get('id')]
    if not ids:
        raise SystemExit('illustrate.py: the xAI account offers no image model')
    return ids[0]


def generate(subject, out):
    key = _key()
    r = requests.post(f'{API}/images/generations', headers={'Authorization': f'Bearer {key}'}, timeout=120,
                      json={'model': model(key), 'prompt': STYLE + subject, 'n': 1, 'response_format': 'b64_json'})
    if r.status_code != 200:
        # xAI's error text explains refusals and billing problems; it never contains the key
        raise SystemExit(f'illustrate.py: xAI images returned HTTP {r.status_code}: {r.text[:300]}')
    item = (r.json().get('data') or [{}])[0]
    if item.get('b64_json'):
        data = base64.b64decode(item['b64_json'])
    elif item.get('url'):
        data = requests.get(item['url'], timeout=60).content
    else:
        raise SystemExit('illustrate.py: xAI returned no image')
    from PIL import Image   # confirm it is a real image before the page embeds it
    import io
    Image.open(io.BytesIO(data)).verify()
    Path(out).write_bytes(data)
    tag = hashlib.sha1(subject.encode()).hexdigest()[:10]
    return {'img': str(out), 'illus': True, 'log': f'grok:{date.today().isoformat()}:{tag} ({subject[:80]})'}


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    print(json.dumps(generate(sys.argv[1], sys.argv[2]), ensure_ascii=False))
