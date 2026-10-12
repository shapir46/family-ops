"""Paint the day's comic with xAI's Grok (Jacob, 2026-10-12). README: "Comic: painted by Grok".

The strip is still composed from the art.py library (edition.json `comic`: scene, cast, poses, faces, gear, props).
This step draws each panel without its bubbles, sends the drawing to Grok's image-edit API to repaint it as a
picture-book illustration (same characters, poses, expressions and places), and saves the result in
painted/<key>.jpg in the work dir. build2.py then uses the painted panels and draws the bubbles on top.

  python repaint.py                 paint every panel not painted yet (reads edition.json in the work dir)
  python repaint.py --redo=2,4      paint panels 2 and 4 again (after a bad result)

A panel's key is a hash of its composition, so rebuilding the page never calls Grok again, and changing a
panel's cast, pose, face, gear, props or scene makes it unpainted until this runs again. build2.py uses the
painted strip only when all four panels are painted; otherwise it prints the drawn strip.
Writes painted/review.jpg: Read it and check every panel (README) before printing.
Needs XAI_API_KEY (never printed). Only the drawing and the cast descriptions below go to xAI: never family facts,
and never the bubble text.
"""
import base64
import io
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import art  # noqa: E402

MODEL = art.PAINT_MODEL

# Fixed descriptions keep the cast looking the same from day to day. Fictional characters only.
LOOKS = {
    'bear': 'Big Bear, a big friendly white polar bear with round ears, a black nose and rosy cheeks',
    'fox': 'Artic, a small white arctic fox with tall pointed ears with pink insides and a big fluffy white tail',
    'mack': 'Mackenzie, a small scruffy apricot (light orange) mini poodle with curly fur and no topknot',
    'uni': 'Uni, a white unicorn who stands on two legs, with a golden horn, lavender hooves and a pastel pink, purple, blue and yellow mane and tail',
    'bob': 'Bob, a small toy figure built from plain plastic bricks, with a yellow round head with a simple drawn face; no brand, no logo',
}
POSE_WORDS = {
    'stand': 'standing', 'wave': 'waving', 'point': 'pointing', 'cheer': 'jumping and cheering with both arms up',
    'shrug': 'shrugging', 'think': 'thinking, one empty paw on the chin and the other empty paw on the tummy', 'run': 'running', 'sit': 'sitting on the ground',
    'hold': 'holding something out', 'tada': 'arms spread wide in a ta-da', 'akimbo': 'hands on hips',
    'facepalm': 'covering the face with one hand', 'dance': 'dancing', 'scared': 'scared with arms up',
}
FACE_WORDS = {
    'happy': 'happy', 'grin': 'grinning', 'laugh': 'laughing', 'surprised': 'surprised', 'sad': 'sad with a tear',
    'worried': 'worried', 'angry': 'grumpy', 'smug': 'smug', 'wink': 'winking', 'sleepy': 'sleepy with eyes closed',
    'love': 'starry-eyed in love', 'proud': 'proud',
}
GEAR_WORDS = {'earmuffs': 'earmuffs over the ears', 'party': 'party hat', 'cape': 'cape', 'shades': 'sunglasses',
              'cap': 'baseball cap', 'beanie': 'knit beanie hat', 'bow': 'hair bow', 'crown': 'crown', 'collar': 'collar'}
COLORS = {'red': (201, 68, 59), 'orange': (232, 130, 58), 'yellow': (245, 200, 60), 'green': (47, 125, 79),
          'light green': (148, 199, 118), 'blue': (59, 111, 182), 'light blue': (143, 211, 230), 'navy': (34, 56, 95),
          'purple': (138, 92, 214), 'lavender': (183, 155, 224), 'pink': (224, 69, 123), 'brown': (122, 90, 53),
          'black': (22, 20, 16), 'white': (250, 250, 250), 'gray': (150, 150, 150), 'gold': (217, 165, 32)}
STYLE = ("Repaint this children's newspaper comic panel as a finished picture-book illustration: soft fluffy fur, smooth "
         "natural rounded arms and legs (no joints, segments or stick limbs), gentle painted shading, clean ink outlines, "
         "warm and cute. Keep every character's species, colors, clothing, held object, pose, facial expression, "
         "position and size exactly as drawn, and keep the background and objects as they are. Characters hold only "
         "the objects named below; a hand that holds nothing stays empty. Hats, glasses, earmuffs and other gear stay on. ")
TAIL = "No text, letters, numbers, speech bubbles, logos, people or extra characters."


def color_name(c):
    if not isinstance(c, str) or not c.startswith('#') or len(c) != 7:
        return ''
    rgb = tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))
    return min(COLORS, key=lambda k: sum((a - b) ** 2 for a, b in zip(COLORS[k], rgb)))


def describe(p):
    """The prompt for one panel: the style, then each character left to right, from the composition only."""
    cast = sorted(p.get('cast', []), key=lambda c: c.get('x', 100))     # mirror flips only the backdrop
    parts = []
    for c in cast:
        k = art.who(c['who']).key
        bits = [POSE_WORDS.get(c.get('pose', 'stand'), 'standing'), FACE_WORDS.get(c.get('face', 'happy'), 'happy')]
        gear = dict(c.get('gear') or {})
        if k == 'mack' and gear.get('collar', True) is not False:
            gear['collar'] = gear.get('collar') if isinstance(gear.get('collar'), str) else art.GEAR_COLOR['collar']
        worn = [f"{color_name(v if isinstance(v, str) else art.GEAR_COLOR.get(g, ''))} {GEAR_WORDS.get(g, g)}".strip()
                for g, v in gear.items() if v]
        if worn:
            bits.append('wearing ' + ', '.join(worn))
        if k == 'bob':
            bits.append(f"in a {color_name(c.get('shirt') or art.Bob.SHIRT)} shirt and blue trousers")
        if c.get('hold'):
            bits.append(f"holding a {c['hold']}")
        parts.append(f"{LOOKS[k]}: {', '.join(bits)}")
    where = {1: ['In the middle'], 2: ['On the left', 'On the right'], 3: ['On the left', 'In the middle', 'On the right']}.get(
        len(parts), ['Next'] * len(parts))
    who = ' '.join(f'{w}, {t}.' for w, t in zip(where, parts))
    return STYLE + who + ' ' + TAIL


def bare_png(panels):
    """Each panel drawn without bubbles or captions, as 1200x732 PNG bytes."""
    from playwright.sync_api import sync_playwright
    out = []
    with sync_playwright() as pw:
        exe = os.environ.get('CHROMIUM_PATH') or ('/opt/pw-browsers/chromium' if os.path.exists('/opt/pw-browsers/chromium') else None)
        b = pw.chromium.launch(executable_path=exe)
        pg = b.new_page(viewport={'width': 600, 'height': 366}, device_scale_factor=2)
        for i, p in enumerate(panels):
            svg = art.panel({**p, 'say': [], 'caption': None, 'paint': False}, i).replace('width="100%"', 'width="600" height="366"')
            pg.set_content(f'<html><body style="margin:0">{svg}</body></html>')
            out.append(pg.screenshot())
        b.close()
    return out


def paint(png, prompt):
    import requests
    import illustrate
    k = illustrate._key()
    r = requests.post(f'{illustrate.API}/images/edits', headers={'Authorization': f'Bearer {k}'}, timeout=240,
                      json={'model': MODEL, 'prompt': prompt, 'response_format': 'b64_json',
                            'image': {'url': 'data:image/png;base64,' + base64.b64encode(png).decode(), 'type': 'image_url'}})
    if r.status_code != 200:
        raise SystemExit(f'xAI image edit returned HTTP {r.status_code}: {r.text[:300]}')
    from PIL import Image
    im = Image.open(io.BytesIO(base64.b64decode(r.json()['data'][0]['b64_json']))).convert('RGB')
    w, h = im.size                                    # Grok returns about the same shape: crop to the panel's exactly
    want = art.W / art.H
    if w / h > want:
        cw = round(h * want); im = im.crop(((w - cw) // 2, 0, (w - cw) // 2 + cw, h))
    else:
        ch = round(w / want); im = im.crop((0, (h - ch) // 2, w, (h - ch) // 2 + ch))
    bio = io.BytesIO()
    im.resize((900, round(900 / want)), Image.LANCZOS).save(bio, 'JPEG', quality=86, optimize=True)
    return bio.getvalue()


def review(panels):
    """painted/review.jpg: the drawn composition (top) over Grok's painting (bottom) for each panel."""
    from PIL import Image, ImageDraw
    rows = []
    for i, (p, drawn) in enumerate(zip(panels, bare_png(panels))):
        a = Image.open(io.BytesIO(drawn)).convert('RGB').resize((600, 366))
        f = art.painted_file(p)
        b = Image.open(f).convert('RGB').resize((600, 366)) if f.exists() else Image.new('RGB', (600, 366), '#ddd')
        rows.append((a, b))
    sheet = Image.new('RGB', (1210, ((len(rows) + 1) // 2) * (2 * 366 + 30)), 'white')
    dr = ImageDraw.Draw(sheet)
    for i, (a, b) in enumerate(rows):
        x, y = (i % 2) * 610, (i // 2) * (2 * 366 + 30)
        dr.text((x + 4, y + 2), f'panel {i + 1}: drawn (top) / painted (bottom)', fill='black')
        sheet.paste(a, (x, y + 14)); sheet.paste(b, (x, y + 14 + 366))
    out = Path('painted') / 'review.jpg'
    sheet.save(out, quality=85)
    return out


def main():
    d = json.loads(Path('edition.json').read_text())
    panels = (d.get('comic') or {}).get('panels') or []
    if len(panels) != 4:
        raise SystemExit('repaint.py: edition.json needs a 4-panel comic first')
    if d['comic'].get('paint') is False:
        raise SystemExit("repaint.py: comic has \"paint\": false; remove it to paint the strip")
    for p in panels:
        for c in p.get('cast', []):
            if art.who(c['who']).key not in LOOKS:
                raise SystemExit(f"repaint.py: no LOOKS description for '{c['who']}'")
    redo = {int(x) - 1 for a in sys.argv[1:] if a.startswith('--redo=') for x in a[7:].split(',') if x}
    Path('painted').mkdir(exist_ok=True)
    todo = [i for i, p in enumerate(panels) if i in redo or not art.painted_file(p).exists()]
    if todo:
        pngs = bare_png([panels[i] for i in todo])

        def one(j):
            i = todo[j]
            art.painted_file(panels[i]).write_bytes(paint(pngs[j], describe(panels[i])))
            return i
        failed = []
        with ThreadPoolExecutor(4) as ex:
            futs = {ex.submit(one, j): todo[j] for j in range(len(todo))}
            for f, i in futs.items():
                try:
                    f.result()
                except BaseException as e:
                    failed.append(f'panel {i + 1}: {e}')
        if failed:
            print('REPAINT FAILED (the drawn strip will print):', '; '.join(failed), file=sys.stderr)
    done = sum(art.painted_file(p).exists() for p in panels)
    print(json.dumps({'painted': done, 'of': 4, 'repainted_now': [i + 1 for i in todo], 'review': str(review(panels))}))
    sys.exit(0 if done == 4 else 1)


if __name__ == '__main__':
    main()
