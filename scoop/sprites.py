"""The painted character library: Grok paints the cast once, the daily comic reuses it (Jacob, 2026-10-12).
README: "Comic: painted character library". The daily run never runs this file and never calls xAI.

Every sprite is painted from the art.py drawing of the same thing, so it lines up with the pose rig:
  body/<char>/<pose>   the character in a pose (happy face, no gear), cut into a body layer (head removed)
                       and a near-arm layer (drawn above the head and props)
  head/<char>/<face>   the head with an expression
  gear/<char>/<gear>   an accessory worn by that character (back, neck or head part)
  held/<name>          a prop held in the paw
  prop/<name>          a scene prop
The drawing goes to Grok's image-edit API on flat magenta; the painting is keyed and cut into layers with masks
made from the drawn parts, so each layer sits exactly where art.py would draw that part. art.py then stacks the
layers for any pose + face + gear + prop combination (art.painted_figure).

  python sprites.py plan [filter...]              list jobs and which are done
  python sprites.py make [filter...] [--redo]     paint the jobs not done yet (filter: bear, head, bear/head, held/rod ...)
  python sprites.py review out.png [filter...]    drawn vs painted side by side, to check before committing
  python sprites.py recut <work dir> [filter...]  cut layers again from a make run's saved paintings (no API call)
Needs XAI_API_KEY (never printed). Only the drawings and the fixed cast descriptions below go to xAI.
"""
import base64
import io
import json
import os
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import art  # noqa: E402

DIR = HERE / 'sprites'
INDEX = DIR / 'index.json'
MODEL = 'grok-imagine-image-2.0'
N = 1024                                    # canvas sent to Grok (square keeps its output aligned)

LOOKS = {
    'bear': 'Big Bear, a big friendly white polar bear with round ears, a black nose and rosy cheeks',
    'fox': 'Artic, a small white arctic fox with tall pointed ears with pink insides and a big fluffy white tail',
    'mack': 'Mackenzie, a small scruffy apricot (light orange) mini poodle with curly fur and no topknot',
    'uni': 'Uni, a white unicorn who stands on two legs, with a golden horn, lavender hooves and a pastel pink, purple, blue and yellow mane and tail',
    'bob': 'Bob, a small toy figure built from plain plastic bricks, with a round yellow head with a simple drawn face, a red shirt and blue trousers; no brand, no logo',
}
POSE_WORDS = {
    'stand': 'standing', 'wave': 'waving', 'point': 'pointing', 'cheer': 'jumping and cheering with both arms up',
    'shrug': 'shrugging', 'think': 'thinking, one empty paw on the chin and the other empty paw on the tummy',
    'run': 'running', 'sit': 'sitting', 'hold': 'holding one empty paw out', 'tada': 'arms spread wide',
    'akimbo': 'hands on hips', 'facepalm': 'covering the face with one paw', 'dance': 'dancing', 'scared': 'scared with arms up',
}
FACE_WORDS = {
    'happy': 'a happy smile', 'grin': 'a big grin', 'laugh': 'laughing', 'surprised': 'a surprised open mouth',
    'sad': 'a sad face with a tear', 'worried': 'a worried face with a sweat drop', 'angry': 'a grumpy face with steam',
    'smug': 'a smug half-lidded smirk', 'wink': 'winking', 'sleepy': 'sleepy with eyes closed and a Z mark',
    'love': 'heart eyes', 'proud': 'a proud smile with eyes closed',
}
GEAR_WORDS = {'scarf': 'a scarf', 'beanie': 'a knit beanie hat', 'earmuffs': 'earmuffs over the ears', 'cap': 'a baseball cap',
              'bow': 'a hair bow', 'party': 'a party hat', 'crown': 'a gold crown', 'glasses': 'round glasses',
              'shades': 'sunglasses', 'cape': 'a cape', 'bowtie': 'a bow tie', 'collar': 'a collar with a round tag'}
BG = ("Keep the background perfectly flat solid magenta (#FF00FF) everywhere: no shadow, no ground, no floor, no gradient, "
      "no texture, no frame. No text or letters, no people, nothing added. ")
STYLE = ("Repaint this cartoon character drawing as a finished children's picture-book illustration: {skin}, smooth "
         "natural rounded arms and legs (no joints, segments or stick limbs), gentle painted shading, clean dark ink "
         "outlines, warm and cute. Keep the exact pose, expression, proportions, outline, position and size so it lines up "
         "with the drawing, and keep every item exactly where it is drawn. " + BG)
OBJ = ("Repaint this cartoon drawing of {what} as a finished children's picture-book illustration: gentle painted "
       "shading, clean dark ink outlines. Keep the exact shape, colors, position and size so it lines up with the drawing. " + BG)

FIG_ORDER = ['legs', 'back', 'gear_back', 'body', 'gear_neck', 'far', 'head', 'gear_head', 'prop', 'near']
GEAR_PART = {'gear_back': 'back', 'gear_neck': 'neck', 'gear_head': 'head'}
TINTED = {'scarf', 'beanie', 'earmuffs', 'cap', 'bow', 'party', 'cape', 'bowtie', 'collar'}
PROP_JOBS = [p for p in art.PROPS if p != 'sfx' and p not in art.HELD or p in ('pumpkin', 'ball', 'basketball', 'gift', 'fish', 'trophy')]


# ---------------------------------------------------------------- jobs
def jobs():
    out = []
    for k in art.CAST:
        out += [f'body/{k}/{p}' for p in art.POSES] + [f'head/{k}/{f}' for f in art.FACES] + [f'gear/{k}/{g}' for g in art.GEAR]
    return out + [f'held/{h}' for h in art.HELD] + [f'prop/{p}' for p in PROP_JOBS]


def pick(filters):
    js = jobs()
    if not filters:
        return js
    return [j for j in js if any(set(f.split('/')) <= set(j.split('/')) for f in filters)]    # 'bear', 'head/bear', 'bear/head', 'held/rod'


def base_gear(k, extra=None):
    g = {'collar': False} if k == 'mack' else {}
    g.update(extra or {})
    return g


def source(job):
    """(layers [(name, svg in root frame)], prompt) for one job."""
    kind, *rest = job.split('/')
    if kind in ('held', 'prop'):
        name = rest[0]
        svg = art.held(name, 0, 0, 1) if kind == 'held' else art.prop(name, 0, 0, 1)
        return [('all', svg)], OBJ.format(what=f'a {name}')
    k, what = rest
    C = art.CAST[k]
    if kind == 'body':
        pose, face, gear = what, 'happy', base_gear(k)
        desc = f'{LOOKS[k]}: {POSE_WORDS[pose]}, with a happy smile.'
    elif kind == 'head':
        pose, face, gear = 'tada', what, base_gear(k)
        desc = f'{LOOKS[k]}: arms spread wide, with {FACE_WORDS[face]}.'
    else:
        pose, face, gear = 'tada', 'happy', base_gear(k, {what: True})
        desc = f'{LOOKS[k]}: arms spread wide, with a happy smile, wearing {GEAR_WORDS[what]}.'
    parts, _ = art.figure_parts(C, pose, face, gear)
    T = art.frames(C, pose)
    layers = [(n, art.grp(svg, T[fr])) for n, svg, fr in parts if n != 'fx' and svg]
    skin = 'smooth glossy plastic' if k == 'bob' else 'soft fluffy fur'
    return layers, STYLE.format(skin=skin) + desc


# ---------------------------------------------------------------- rendering (playwright) and masks (Pillow only)
class Renderer:
    def __enter__(self):
        from playwright.sync_api import sync_playwright
        self.pw = sync_playwright().start()
        exe = os.environ.get('CHROMIUM_PATH') or ('/opt/pw-browsers/chromium' if os.path.exists('/opt/pw-browsers/chromium') else None)
        self.b = self.pw.chromium.launch(executable_path=exe)
        self.pg = self.b.new_page(viewport={'width': N, 'height': N})
        return self

    def __exit__(self, *a):
        self.b.close()
        self.pw.stop()

    def bbox(self, svg):
        self.pg.set_content(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-500 -500 1000 1000"><g id="c">{svg}</g></svg>')
        return self.pg.evaluate("(() => { const b = document.getElementById('c').getBBox(); return [b.x, b.y, b.width, b.height]; })()")

    def png(self, svg, vb, bg=None):
        from PIL import Image
        x, y, L = vb
        fill = f'<rect x="{x}" y="{y}" width="{L}" height="{L}" fill="{bg}"/>' if bg else ''
        self.pg.set_content(f'<html><body style="margin:0;background:transparent"><svg xmlns="http://www.w3.org/2000/svg" '
                            f'viewBox="{x} {y} {L} {L}" width="{N}" height="{N}" style="display:block">{fill}{svg}</svg></body></html>')
        return Image.open(io.BytesIO(self.pg.screenshot(omit_background=bg is None))).convert('RGBA')


def alpha(im):
    return im.getchannel('A').point(lambda v: 255 if v > 8 else 0)


def dilate(m, px):
    from PIL import ImageFilter
    size = max(1, int(round(px))) * 2 + 1
    while size > 1:                                  # MaxFilter is slow for large sizes: grow in steps of at most 9
        step = min(size, 9)
        m = m.filter(ImageFilter.MaxFilter(step))
        size -= step - 1
    return m


def union(ms):
    from PIL import ImageChops
    out = None
    for m in ms:
        out = m if out is None else ImageChops.lighter(out, m)
    return out


def key(painted):
    """Alpha from the flat magenta background, and the painting with magenta spill removed at the edges."""
    from PIL import ImageChops, Image
    R, G, B = painted.convert('RGB').split()
    mag = ImageChops.subtract(ImageChops.darker(R, B), G)            # 0 for any normal color, ~255 for magenta
    a = mag.point(lambda v: 255 if v < 70 else 0 if v > 150 else int(255 * (150 - v) / 80))
    spill = mag.point(lambda v: max(0, v - 25))
    edge = a.point(lambda v: 255 if v < 250 else 0)
    R2, B2 = ImageChops.subtract(R, spill), ImageChops.subtract(B, spill)
    out = Image.merge('RGB', (Image.composite(R2, R, edge), G, Image.composite(B2, B, edge)))
    return out, a


# ---------------------------------------------------------------- painting
def paint(png_bytes, prompt):
    import requests
    import illustrate
    k = illustrate._key()
    last = None
    for _ in range(3):
        try:
            r = requests.post(f'{illustrate.API}/images/edits', headers={'Authorization': f'Bearer {k}'}, timeout=300,
                              json={'model': MODEL, 'prompt': prompt, 'response_format': 'b64_json',
                                    'image': {'url': 'data:image/png;base64,' + base64.b64encode(png_bytes).decode(), 'type': 'image_url'}})
            if r.status_code == 200:
                from PIL import Image
                im = Image.open(io.BytesIO(base64.b64decode(r.json()['data'][0]['b64_json']))).convert('RGB')
                w, h = im.size
                s = min(w, h)
                return im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s)).resize((N, N), Image.LANCZOS)
            last = f'HTTP {r.status_code}: {r.text[:200]}'
        except Exception as e:  # network hiccup: retry
            last = str(e)
    raise RuntimeError(f'xAI image edit failed: {last}')


def prepare(R, job, work):
    """Draw the job's source on magenta and its part masks; returns the view box."""
    layers, prompt = source(job)
    allsvg = ''.join(s for _, s in layers)
    x, y, w, h = R.bbox(allsvg)
    m = 7                                             # room for fur fluff past the drawn outline
    L = max(w, h) + 2 * m
    vb = (x + w / 2 - L / 2, y + h / 2 - L / 2, L)
    d = work / job.replace('/', '_')
    d.mkdir(parents=True, exist_ok=True)
    src = R.png(allsvg, vb, '#ff00ff').convert('RGB')
    src.save(d / 'src.png')
    alpha(R.png(allsvg, vb)).save(d / 'm_all.png')
    for n, s in layers:
        if n != 'all':
            alpha(R.png(s, vb)).save(d / f'm_{n}.png')
    (d / 'job.json').write_text(json.dumps({'job': job, 'vb': vb, 'prompt': prompt, 'parts': [n for n, _ in layers]}))
    return d


def cut(d):
    """Key the painting and cut it into layers; returns {sprite key: (RGBA image, (x, y, w, h) in root units)}."""
    from PIL import Image, ImageChops
    meta = json.loads((d / 'job.json').read_text())
    job, (vx, vy, L), parts = meta['job'], meta['vb'], meta['parts']
    ppu = N / L                                      # pixels per unit on the canvas
    rgb, a = key(Image.open(d / 'painted.png'))
    M = {n: Image.open(d / f'm_{n}.png').convert('L') for n in ['all'] + [p for p in parts if p != 'all']}
    above = lambda n: union([M[p] for p in parts if p in FIG_ORDER and FIG_ORDER.index(p) > FIG_ORDER.index(n)])

    def visible(n):
        up = above(n)
        return M[n] if up is None else ImageChops.subtract(M[n], up)

    def layer(mask):
        return ImageChops.darker(a, mask)
    fluff = 1.6 * ppu
    kind, *rest = job.split('/')
    out = {}
    if kind in ('held', 'prop'):
        out[job] = layer(dilate(M['all'], fluff))
    elif kind == 'body':
        k, pose = rest
        body = ImageChops.subtract(layer(dilate(M['all'], fluff)), M['head'])
        out[f'{k}/body/{pose}'] = body
        out[f'{k}/near/{pose}'] = layer(dilate(M['near'], .5 * ppu))
    elif kind == 'head':
        k, face = rest
        out[f'{k}/head/{face}'] = layer(dilate(visible('head'), fluff))
    else:
        k, g = rest
        for n in ('gear_back', 'gear_neck', 'gear_head'):
            if n in M:
                out[f'{k}/gear/{g}/{GEAR_PART[n]}'] = layer(dilate(visible(n), .3 * ppu))   # tight: gear gets recolored
    res = {}
    for sk, am in out.items():
        bb = am.getbbox()
        if not bb:
            continue
        im = rgb.copy()
        im.putalpha(am)
        im = im.crop(bb)
        res[sk] = (im, (vx + bb[0] / ppu, vy + bb[1] / ppu, (bb[2] - bb[0]) / ppu, (bb[3] - bb[1]) / ppu))
    return res


def store(res, job):
    from PIL import Image
    idx = load()
    for sk, (im, (x, y, w, h)) in res.items():
        scale = min(1.0, max(4.0 * w, 160) / im.width)      # keep about 4 px per unit (2x print), at least 160 px wide
        if scale < 1:
            im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.LANCZOS)
        f = sk.replace('/', '-') + '.webp'
        (DIR / sk.split('/')[0]).mkdir(parents=True, exist_ok=True)
        rel = f'{sk.split("/")[0]}/{f}'
        im.save(DIR / rel, 'WEBP', quality=86, method=6)
        idx['sprites'][sk] = {'file': rel, 'x': round(x, 2), 'y': round(y, 2), 'w': round(w, 2), 'h': round(h, 2)}
    idx['jobs'][job] = {'model': MODEL, 'made': date.today().isoformat()}
    save(idx)


def load():
    return json.loads(INDEX.read_text()) if INDEX.exists() else {'sprites': {}, 'jobs': {}}


def save(idx):
    DIR.mkdir(exist_ok=True)
    INDEX.write_text(json.dumps({'sprites': dict(sorted(idx['sprites'].items())), 'jobs': dict(sorted(idx['jobs'].items()))},
                                indent=0, ensure_ascii=False) + '\n')


def make(filters, redo=False, threads=8):
    todo = [j for j in pick(filters) if redo or j not in load()['jobs']]
    print(f'{len(todo)} jobs to paint', file=sys.stderr)
    if not todo:
        return
    work = Path(os.environ.get('SPRITE_WORK') or tempfile.mkdtemp(prefix='sprites-'))
    with Renderer() as R:
        dirs = {j: prepare(R, j, work) for j in todo}

    def one(j):
        d = dirs[j]
        meta = json.loads((d / 'job.json').read_text())
        paint((d / 'src.png').read_bytes(), meta['prompt']).save(d / 'painted.png')
        return j
    failed = []
    with ThreadPoolExecutor(threads) as ex:
        futs = {ex.submit(one, j): j for j in todo}
        for f, j in futs.items():
            try:
                f.result()
                store(cut(dirs[j]), j)
                print('painted', j, file=sys.stderr)
            except Exception as e:
                failed.append(j)
                print('FAILED', j, e, file=sys.stderr)
    print(json.dumps({'painted': len(todo) - len(failed), 'failed': failed, 'work': str(work)}))


def review(out, filters):
    """Drawn (left) and painted (right) for each job, as one PNG to Read before committing."""
    from PIL import Image, ImageDraw
    idx = load()
    art.SPRITES.clear(); art.SPRITES.update(idx['sprites']); art.SPRITE_JOBS.clear(); art.SPRITE_JOBS.update(idx['jobs'])
    js = [j for j in pick(filters) if j in idx['jobs']]
    cells = []
    with Renderer() as R:
        for j in js:
            layers, _ = source(j)
            allsvg = ''.join(s for _, s in layers)
            x, y, w, h = R.bbox(allsvg)
            L = max(w, h) + 14
            vb = (x + w / 2 - L / 2, y + h / 2 - L / 2, L)
            drawn = R.png(allsvg, vb, '#ffffff').convert('RGB').resize((240, 240))
            kind, *rest = j.split('/')
            if kind == 'body':                       # the body and near-arm layers (no head: heads are their own jobs)
                k, pose = rest
                svg = art.sprite(f'{k}/body/{pose}') + art.sprite(f'{k}/near/{pose}')
            elif kind in ('head', 'gear'):           # the cut layers, in the tada frame they were painted in
                k, what = rest
                pre = f'{k}/head/{what}' if kind == 'head' else f'{k}/gear/{what}/'
                svg = ''.join(art.sprite(sk) for sk in art.SPRITES if sk == pre or sk.startswith(pre))
            else:
                svg = art.painted_prop(rest[0], 0, 0, 1, held=kind == 'held') or ''
            painted = R.png(svg, vb, '#ffffff').convert('RGB').resize((240, 240))
            c = Image.new('RGB', (490, 262), 'white')
            c.paste(drawn, (0, 20)); c.paste(painted, (250, 20))
            ImageDraw.Draw(c).text((4, 4), j, fill='black')
            cells.append(c)
    cols = 4
    sheet = Image.new('RGB', (cols * 500, ((len(cells) + cols - 1) // cols) * 270), 'white')
    for i, c in enumerate(cells):
        sheet.paste(c, ((i % cols) * 500, (i // cols) * 270))
    sheet.save(out)
    print('wrote', out, len(cells), 'jobs')


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if args[:1] == ['plan']:
        done = load()['jobs']
        js = pick(args[1:])
        for j in js:
            print(('done ' if j in done else 'todo ') + j)
        print(f'{sum(j in done for j in js)}/{len(js)} done', file=sys.stderr)
    elif args[:1] == ['make']:
        make(args[1:], redo='--redo' in sys.argv)
    elif args[:1] == ['recut'] and len(args) >= 2:
        for d in sorted(Path(args[1]).iterdir()):
            if (d / 'painted.png').exists():
                j = json.loads((d / 'job.json').read_text())['job']
                if j in pick(args[2:]):
                    store(cut(d), j)
                    print('recut', j)
    elif args[:1] == ['review'] and len(args) >= 2:
        review(args[1], args[2:])
    else:
        raise SystemExit(__doc__)
