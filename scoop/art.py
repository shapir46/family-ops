"""Comic art for the Fairfax Daily Scoop: an original character library (SVG, no third-party characters).

The cast stands upright on a rig (shoulders, elbows, hips, knees), so any character can take any POSE,
wear any FACE and GEAR and hold a HELD prop. A daily strip is data, not code: edition.json `comic`
picks a scene, places the cast and writes the bubbles (README: "Comic"). Nothing here is family data.

  python art.py --list               print the library (cast, poses, faces, gear, held, props, scenes)
  python art.py --sheet cast.html    draw a model sheet of every character, pose, face, prop and scene

Scenes are drawn here (SCENES) or painted: PAINTED backdrops are Grok-made scenery in backdrops/ (backdrops.py;
README: "Comic: painted backdrops"). Each day repaint.py has Grok repaint the composed panels, characters included
(README: "Comic: painted by Grok"); the composition, and the drawn fallback, always come from here.
"""
import base64
import html as _html
import json
import math
import re
import sys
from pathlib import Path

INK = '#161410'
W, H = 200, 122                      # panel viewBox


# ---------------------------------------------------------------- SVG helpers
def fmt(v):
    return (f'{v:.2f}'.rstrip('0').rstrip('.') or '0') if isinstance(v, float) else str(v)


def el(tag, inner=None, **a):
    at = ' '.join(f'{k.rstrip("_").replace("_", "-")}="{fmt(v)}"' for k, v in a.items() if v is not None)
    return f'<{tag} {at}>{inner}</{tag}>' if inner is not None else f'<{tag} {at}/>'


def circ(cx, cy, r, fill, sw=1.3, stroke=INK, **k):
    return el('circle', cx=cx, cy=cy, r=r, fill=fill, stroke=stroke if sw else None, stroke_width=sw or None, **k)


def ell(cx, cy, rx, ry, fill, sw=1.3, stroke=INK, **k):
    return el('ellipse', cx=cx, cy=cy, rx=rx, ry=ry, fill=fill, stroke=stroke if sw else None, stroke_width=sw or None, **k)


def pth(d, fill='none', sw=1.3, stroke=INK, **k):
    return el('path', d=d, fill=fill, stroke=stroke if sw else None, stroke_width=sw or None,
              stroke_linejoin='round', stroke_linecap='round', **k)


def rct(x, y, w, h, fill, sw=1.3, rx=0, stroke=INK, **k):
    return el('rect', x=x, y=y, width=w, height=h, rx=rx or None, fill=fill, stroke=stroke if sw else None,
              stroke_width=sw or None, **k)


def grp(inner, t=None, **k):
    return el('g', inner, transform=t, **k)


def rot(x, y, deg):
    r = math.radians(deg)
    return x * math.cos(r) - y * math.sin(r), x * math.sin(r) + y * math.cos(r)


def crescent(cx, cy, rx, ry, color, t1=-55, t2=150, depth=.32, op=1.0):
    """Shadow crescent inside an ellipse, on the lower right (light comes from the upper left)."""
    p = lambda t: (cx + rx * math.cos(math.radians(t)), cy + ry * math.sin(math.radians(t)))
    (x1, y1), (x2, y2) = p(t1), p(t2)
    large = 1 if (t2 - t1) > 180 else 0
    qx, qy = cx + rx * depth * .6, cy + ry * depth * .4
    return pth(f'M{x1:.1f},{y1:.1f} A{rx:.1f},{ry:.1f} 0 {large} 1 {x2:.1f},{y2:.1f} Q{qx:.1f},{qy:.1f} {x1:.1f},{y1:.1f} Z',
               color, 0, opacity=op if op < 1 else None)


def curly(cx, cy, rx, ry, fill, n=None, sw=1.1, stroke=INK, phase=0.0, depth=.62):
    """Scalloped blob: a ring of small arcs. Curly poodle fur, clouds, tree tops, bushes."""
    if n is None:
        n = max(7, int(2 * math.pi * math.sqrt((rx * rx + ry * ry) / 2) / 4.4))
    pts = [(cx + rx * math.cos(2 * math.pi * k / n + phase), cy + ry * math.sin(2 * math.pi * k / n + phase)) for k in range(n + 1)]
    d = f'M{pts[0][0]:.1f},{pts[0][1]:.1f}'
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        r = math.hypot(x1 - x0, y1 - y0) * depth
        d += f' A{r:.1f},{r:.1f} 0 0 1 {x1:.1f},{y1:.1f}'
    return pth(d + ' Z', fill, sw, stroke)


def curls(spots, color, sw=.8):
    """Little curl marks for fur texture: spots = [(x, y, r), ...]."""
    return pth(' '.join(f'M{x - r:.1f},{y:.1f} a{r:.1f},{r:.1f} 0 1 1 {r * 1.5:.1f},{r * .9:.1f}' for x, y, r in spots), 'none', sw, color)


def tufts(spots, color, sw=.8):
    """Little 'v' fur strokes: spots = [(x, y, size), ...]."""
    return pth(' '.join(f'M{x - s:.1f},{y - s * .5:.1f} L{x:.1f},{y + s * .6:.1f} L{x + s:.1f},{y - s * .5:.1f}' for x, y, s in spots), 'none', sw, color)


def limb(pts, w, fill, sw=1.3):
    """A seamless outlined limb along a polyline (outline stroke under a fill stroke)."""
    p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
    return (el('polyline', points=p, fill='none', stroke=INK, stroke_width=w + 2 * sw, stroke_linecap='round', stroke_linejoin='round') +
            el('polyline', points=p, fill='none', stroke=fill, stroke_width=w, stroke_linecap='round', stroke_linejoin='round'))


def esc(t):
    return re.sub(r'&(?!#?\w+;)', '&amp;', str(t)).replace('<', '&lt;').replace('>', '&gt;')


# ---------------------------------------------------------------- poses
# Arms: (shoulder angle from straight down, outward +; elbow bend, + bends up/outward, - bends inward)
#       or a target the paw reaches: 'chin', 'face', 'belly', 'hip'.
# Legs: (hip angle outward +; knee bend). dy lifts the whole body (-), tilt tips the head, lean tips the body
# toward the way the character faces. fx = motion marks.
POSES = {
    'stand':    dict(R=(12, 8), L=(12, 8), RL=(3, 0), LL=(3, 0)),
    'wave':     dict(R=(135, 20), L=(12, 8), RL=(3, 0), LL=(3, 0), tilt=-6, fx='wave'),
    'point':    dict(R=(94, 4), L=(14, 10), RL=(5, 0), LL=(3, 0)),
    'cheer':    dict(R=(158, 14), L=(158, 14), RL=(26, -46), LL=(26, -46), dy=-9, fx='jump'),
    'shrug':    dict(R=(62, 80), L=(62, 80), RL=(4, 0), LL=(4, 0), tilt=10),
    'think':    dict(R='chin', L='belly', RL=(3, 0), LL=(3, 0), tilt=-8),
    'run':      dict(R=(70, 60), L=(42, -55), RL=(40, -40), LL=(30, 75), lean=9, fx='speed'),
    'sit':      dict(R=(22, -60), L=(22, -60), sit=True),
    'hold':     dict(R=(48, 55), L=(12, 8), RL=(3, 0), LL=(3, 0)),
    'tada':     dict(R=(112, -12), L=(112, -12), RL=(9, 0), LL=(9, 0)),
    'akimbo':   dict(R='hip', L='hip', RL=(9, 0), LL=(9, 0), tilt=-4),
    'facepalm': dict(R='face', L=(12, 8), RL=(3, 0), LL=(3, 0), tilt=9),
    'dance':    dict(R=(145, 25), L=(72, -60), RL=(48, -100), LL=(4, 0), tilt=10, lean=-6, fx='notes'),
    'scared':   dict(R=(130, 70), L=(130, 70), RL=(14, 0), LL=(14, 0), dy=-4, fx='shake'),
}

# Faces: (eyes, mouth, brows) + an extra mark
FACES = {
    'happy':     ('open', 'smile', None, None),
    'grin':      ('open', 'grin', 'up', None),
    'laugh':     ('happy', 'laugh', None, 'blush'),
    'surprised': ('wide', 'o', 'high', None),
    'sad':       ('open', 'frown', 'sad', 'tear'),
    'worried':   ('open', 'wavy', 'sad', 'sweat'),
    'angry':     ('open', 'frown', 'angry', 'steam'),
    'smug':      ('half', 'smirk', None, None),
    'wink':      ('wink', 'grin', None, None),
    'sleepy':    ('closed', 'flat', None, 'zzz'),
    'love':      ('heart', 'smile', None, 'blush'),
    'proud':     ('happy', 'smile', 'up', 'blush'),
}


def ik(S, T, L1, L2, side):
    """Two-link reach from shoulder S to target T; the elbow bends outward."""
    dx, dy = T[0] - S[0], T[1] - S[1]
    d = max(abs(L1 - L2) + .01, min(L1 + L2 - .01, math.hypot(dx, dy)))
    a = math.atan2(dy, dx)
    b = math.acos(max(-1, min(1, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d))))
    cands = [(S[0] + L1 * math.cos(a + s * b), S[1] + L1 * math.sin(a + s * b)) for s in (1, -1)]
    E = max(cands, key=lambda e: side * e[0] + e[1] * .25)
    ang = math.atan2(dy, dx)
    Hx, Hy = S[0] + d * math.cos(ang), S[1] + d * math.sin(ang)
    return E, (Hx, Hy)


def fk(S, side, a1, a2, L1, L2):
    r1 = -a1 * side
    r2 = r1 - a2 * side
    ex, ey = rot(0, L1, r1)
    E = (S[0] + ex, S[1] + ey)
    hx, hy = rot(0, L2, r2)
    return E, (E[0] + hx, E[1] + hy)


# ---------------------------------------------------------------- faces
def eye(kind, x, y, r, lid, lash, side):
    hl = circ(x - r * .28, y - r * .38, r * .34, '#fff', 0) + circ(x + r * .25, y + r * .35, r * .14, '#fff', 0)
    if kind == 'open':
        out = ell(x, y, r * .78, r, INK, 0) + hl
    elif kind == 'wide':
        out = ell(x, y, r * 1.05, r * 1.3, '#fff', r * .32) + circ(x + r * .1, y + r * .1, r * .5, INK, 0) + circ(x - r * .05, y - r * .1, r * .16, '#fff', 0)
    elif kind == 'happy':
        out = pth(f'M{x - r * .95:.1f},{y + r * .35:.1f} Q{x:.1f},{y - r * 1.2:.1f} {x + r * .95:.1f},{y + r * .35:.1f}', 'none', r * .55)
    elif kind == 'closed':
        out = pth(f'M{x - r * .95:.1f},{y - r * .1:.1f} Q{x:.1f},{y + r * .85:.1f} {x + r * .95:.1f},{y - r * .1:.1f}', 'none', r * .5)
    elif kind == 'half':
        out = (ell(x, y, r * .78, r, INK, 0) + hl +
               pth(f'M{x - r * 1.1:.1f},{y - r * 1.3:.1f} H{x + r * 1.1:.1f} V{y - r * .05:.1f} H{x - r * 1.1:.1f} Z', lid, 0) +
               pth(f'M{x - r * .95:.1f},{y - r * .05:.1f} H{x + r * .95:.1f}', 'none', r * .45))
    elif kind == 'heart':
        s = r * 1.15
        out = pth(f'M{x:.1f},{y + s * .9:.1f} C{x - s * 1.6:.1f},{y - s * .1:.1f} {x - s * .7:.1f},{y - s * 1.3:.1f} {x:.1f},{y - s * .4:.1f} '
                  f'C{x + s * .7:.1f},{y - s * 1.3:.1f} {x + s * 1.6:.1f},{y - s * .1:.1f} {x:.1f},{y + s * .9:.1f} Z', '#e0457b', r * .25)
    else:
        out = ''
    if lash and kind in ('open', 'wide', 'half', 'happy'):
        ox = x + side * r * .7
        out += pth(f'M{ox:.1f},{y - r * .7:.1f} l{side * r * .7:.1f},{-r * .55:.1f} M{ox - side * r * .3:.1f},{y - r * .95:.1f} l{side * r * .35:.1f},{-r * .75:.1f}', 'none', r * .3)
    return out


def brow(kind, x, y, r, side):
    """side: -1 = left eye (inner end on the right), +1 = right eye."""
    b = y - r * 1.85
    xi, xo = x - side * r * .75, x + side * r * .75            # inner, outer ends
    lift = {'up': (.45, .45), 'high': (1.1, 1.0), 'sad': (1.0, -.15), 'angry': (-.55, .55)}[kind]
    yi, yo = b - lift[0] * r, b - lift[1] * r
    mx, my = (xi + xo) / 2, min(yi, yo) - r * .35 * (kind in ('up', 'high'))
    return pth(f'M{xi:.1f},{yi:.1f} Q{mx:.1f},{my:.1f} {xo:.1f},{yo:.1f}', 'none', r * .42)


def mouth(kind, x, y, w, lw):
    dark, tongue = '#7a2430', '#f08a9a'
    if kind == 'smile':
        return pth(f'M{x - w / 2:.1f},{y - w * .08:.1f} Q{x:.1f},{y + w * .42:.1f} {x + w / 2:.1f},{y - w * .08:.1f}', 'none', lw)
    if kind in ('grin', 'laugh'):
        k = .8 if kind == 'grin' else 1.05
        hw = w / 2 if kind == 'grin' else w * .6
        d = f'M{x - hw:.1f},{y - w * .1:.1f} Q{x:.1f},{y + w * k:.1f} {x + hw:.1f},{y - w * .1:.1f} Z'
        ty = y - w * .1 + (w * k + w * .1) * .5 - w * .13
        return pth(d, dark, lw * .9) + ell(x, ty, w * .2, w * .1, tongue, 0) + pth(d, 'none', lw * .9)
    if kind == 'o':
        return ell(x, y + w * .12, w * .17, w * .23, dark, lw * .8)
    if kind == 'frown':
        return pth(f'M{x - w * .4:.1f},{y + w * .22:.1f} Q{x:.1f},{y - w * .25:.1f} {x + w * .4:.1f},{y + w * .22:.1f}', 'none', lw)
    if kind == 'wavy':
        return pth(f'M{x - w * .45:.1f},{y + w * .05:.1f} q{w * .15:.1f},{-w * .2:.1f} {w * .3:.1f},0 t{w * .3:.1f},0 t{w * .3:.1f},0', 'none', lw)
    if kind == 'smirk':
        return pth(f'M{x - w * .35:.1f},{y + w * .02:.1f} Q{x + w * .12:.1f},{y + w * .3:.1f} {x + w * .5:.1f},{y - w * .2:.1f}', 'none', lw)
    if kind == 'flat':
        return pth(f'M{x - w * .2:.1f},{y + w * .05:.1f} H{x + w * .2:.1f}', 'none', lw)
    return ''


def draw_face(C, kind, with_mouth=True):
    eyes, mth, brows, extra = FACES.get(kind, FACES['happy'])
    cx, cy, sp, r = C.eyes
    out = ''
    blush_op = .75 if extra == 'blush' else .45
    out += ''.join(ell(x, y, rx, rx * .6, C.blush, 0, opacity=blush_op) for x, y, rx in C.cheeks)
    for side, ex in ((-1, cx - sp), (1, cx + sp)):
        k = eyes if not (eyes == 'wink' and side == 1) else 'happy'
        if eyes == 'wink' and side == -1:
            k = 'open'
        rr = r * (.92 if side == -1 else 1)
        out += eye(k, ex, cy, rr, C.lid, C.lash, side)
        if brows:
            out += brow(brows, ex, cy, rr, side)
    mx, my, mw = C.mouth
    if with_mouth:
        out += mouth(mth, mx, my, mw, C.lw)
    hx, hy, hr = C.head
    if extra == 'tear':
        tx, ty = cx + sp + r * .2, cy + r * 1.6
        out += pth(f'M{tx:.1f},{ty:.1f} q{-r * .9:.1f},{r * 1.6:.1f} 0,{r * 1.9:.1f} q{r * .9:.1f},{-r * .3:.1f} 0,{-r * 1.9:.1f} Z', '#8fc7ec', r * .25)
    if extra == 'sweat':
        tx, ty = hx + hr * 1.02, hy - hr * .55
        out += pth(f'M{tx:.1f},{ty:.1f} q{-r * 1.2:.1f},{r * 2:.1f} 0,{r * 2.4:.1f} q{r * 1.2:.1f},{-r * .4:.1f} 0,{-r * 2.4:.1f} Z', '#8fc7ec', r * .3)
    if extra == 'zzz':
        zx = lambda i: hx + hr * (.95 + .45 * i)
        z = ''.join(el('text', 'z', x=zx(i), y=hy - hr * (.85 + .55 * i), font_size=hr * (.7 + .22 * i), font_family='PF, serif', font_weight=700,
                       fill='#3b6fb6', transform=f'translate({2 * zx(i):.1f},0) scale(-1,1)' if getattr(C, '_flip', False) else None) for i in range(3))
        out += z
    if extra == 'steam':
        sx, sy = hx + hr * .95, hy - hr * .95
        out += pth(f'M{sx:.1f},{sy:.1f} q{hr * .25:.1f},{-hr * .2:.1f} 0,{-hr * .4:.1f} t0,{-hr * .4:.1f} '
                   f'M{sx + hr * .35:.1f},{sy + hr * .2:.1f} q{hr * .25:.1f},{-hr * .2:.1f} 0,{-hr * .4:.1f} t0,{-hr * .4:.1f}', 'none', hr * .07, '#9a9a9a')
    return out


# ---------------------------------------------------------------- gear (hats, scarves, capes, glasses)
GEAR = ['scarf', 'beanie', 'earmuffs', 'cap', 'bow', 'party', 'crown', 'glasses', 'shades', 'cape', 'bowtie', 'collar']
GEAR_COLOR = {'scarf': '#c9443b', 'beanie': '#3b6fb6', 'earmuffs': '#d9534f', 'cap': '#2f7d4f', 'bow': '#e0457b',
              'party': '#8a5cd6', 'cape': '#c9443b', 'bowtie': '#2f5aa8', 'collar': '#b79be0'}


def dark(c, k=.72):
    c = c.lstrip('#')
    return '#' + ''.join(f'{int(int(c[i:i + 2], 16) * k):02x}' for i in (0, 2, 4))


def gear_back(C, gear):
    out = ''
    if gear.get('cape'):
        col = gear['cape'] if isinstance(gear['cape'], str) else GEAR_COLOR['cape']
        nx, ny, nw = C.neck
        sx = C.shoulder[0]
        by = C.hip[1] + 14
        out += pth(f'M{nx - nw * .45:.1f},{ny:.1f} C{-sx * 1.9:.1f},{ny + 2:.1f} {-sx * 2.7:.1f},{by - 18:.1f} {-sx * 2.6:.1f},{by:.1f} '
                   f'Q{-sx * 2.1:.1f},{by - 5:.1f} {-sx * 1.7:.1f},{by + 2:.1f} Q{-sx * 1.2:.1f},{by - 4:.1f} {-sx * .7:.1f},{by + 2:.1f} '
                   f'L{sx * 1.15:.1f},{by:.1f} Q{sx * 1.3:.1f},{ny + 10:.1f} {nx + nw * .45:.1f},{ny:.1f} Z', col, 1.2)
        out += pth(f'M{-sx * 2.0:.1f},{by - 4:.1f} Q{-sx * 1.7:.1f},{(ny + by) / 2:.1f} {-sx * 1.0:.1f},{ny + 6:.1f} '
                   f'M{-sx * 1.4:.1f},{by - 2:.1f} Q{-sx * 1.2:.1f},{(ny + by) / 2 + 6:.1f} {-sx * .6:.1f},{ny + 10:.1f}', 'none', .8, dark(col))
    return out


def gear_neck(C, gear):
    out = ''
    nx, ny, w = C.neck
    if gear.get('scarf'):
        col = gear['scarf'] if isinstance(gear['scarf'], str) else GEAR_COLOR['scarf']
        d = dark(col)
        out += pth(f'M{nx - w / 2:.1f},{ny - 2:.1f} Q{nx:.1f},{ny + w * .18:.1f} {nx + w / 2:.1f},{ny - 2:.1f} '
                   f'L{nx + w / 2:.1f},{ny + w * .1:.1f} Q{nx:.1f},{ny + w * .34:.1f} {nx - w / 2:.1f},{ny + w * .1:.1f} Z', col, 1.1)
        tx, ty, tw, th = nx + w * .14, ny + w * .16, w * .2, w * .55
        out += pth(f'M{tx:.1f},{ty:.1f} L{tx + tw:.1f},{ty - 1:.1f} L{tx + tw + 1.5:.1f},{ty + th:.1f} L{tx + 1:.1f},{ty + th + 1:.1f} Z', col, 1.1)
        out += pth(f'M{tx + .5:.1f},{ty + th * .45:.1f} L{tx + tw + .8:.1f},{ty + th * .42:.1f} M{tx + .7:.1f},{ty + th * .7:.1f} L{tx + tw + 1.1:.1f},{ty + th * .67:.1f}', 'none', w * .045, d)
        out += pth(' '.join(f'M{tx + 1 + i * tw / 3:.1f},{ty + th + .8:.1f} l0,{w * .07:.1f}' for i in range(4)), 'none', .8)
    if gear.get('cape'):
        col = gear['cape'] if isinstance(gear['cape'], str) else GEAR_COLOR['cape']
        out += pth(f'M{nx - w * .5:.1f},{ny - 1:.1f} L{nx - w * .12:.1f},{ny + w * .12:.1f} L{nx - w * .38:.1f},{ny + w * .22:.1f} Z '
                   f'M{nx + w * .5:.1f},{ny - 1:.1f} L{nx + w * .12:.1f},{ny + w * .12:.1f} L{nx + w * .38:.1f},{ny + w * .22:.1f} Z', col, 1)
        out += circ(nx, ny + w * .12, w * .08, '#f5cf55', .9)
    if gear.get('collar'):
        col = gear['collar'] if isinstance(gear['collar'], str) else GEAR_COLOR['collar']
        out += pth(f'M{nx - w / 2:.1f},{ny - 1:.1f} Q{nx:.1f},{ny + w * .16:.1f} {nx + w / 2:.1f},{ny - 1:.1f} '
                   f'L{nx + w / 2:.1f},{ny + w * .07:.1f} Q{nx:.1f},{ny + w * .25:.1f} {nx - w / 2:.1f},{ny + w * .07:.1f} Z', col, 1)
        out += circ(nx + w * .05, ny + w * .3, w * .1, '#f2c94c', .9) + circ(nx + w * .05, ny + w * .3, w * .035, dark('#f2c94c'), 0)
    if gear.get('bowtie'):
        col = gear['bowtie'] if isinstance(gear['bowtie'], str) else GEAR_COLOR['bowtie']
        s = w * .16
        out += pth(f'M{nx:.1f},{ny + s * .4:.1f} L{nx - s * 1.6:.1f},{ny - s * .6:.1f} L{nx - s * 1.6:.1f},{ny + s * 1.4:.1f} Z '
                   f'M{nx:.1f},{ny + s * .4:.1f} L{nx + s * 1.6:.1f},{ny - s * .6:.1f} L{nx + s * 1.6:.1f},{ny + s * 1.4:.1f} Z', col, 1)
        out += circ(nx, ny + s * .4, s * .45, dark(col), 1)
    return out


def gear_head(C, gear):
    out = ''
    cx, cy, r = C.head
    g = lambda k: gear[k] if isinstance(gear.get(k), str) else GEAR_COLOR.get(k, '#c9443b')
    if gear.get('beanie'):
        col = g('beanie')
        out += pth(f'M{cx - r * 1.04:.1f},{cy - r * .42:.1f} Q{cx - r:.1f},{cy - r * 1.48:.1f} {cx:.1f},{cy - r * 1.5:.1f} '
                   f'Q{cx + r:.1f},{cy - r * 1.48:.1f} {cx + r * 1.04:.1f},{cy - r * .42:.1f} Z', col, 1.2)
        out += crescent(cx, cy - r * .55, r * 1.0, r * .9, dark(col, .85), t1=-80, t2=0, depth=.5)
        out += rct(cx - r * 1.12, cy - r * .62, r * 2.24, r * .34, dark(col, .82), 1.1, rx=r * .15)
        out += pth(' '.join(f'M{cx - r + i * r / 4:.1f},{cy - r * .58:.1f} v{r * .26:.1f}' for i in range(9)), 'none', .6, dark(col, .6))
        out += curly(cx, cy - r * 1.58, r * .3, r * .28, '#fbfaf3', n=8, sw=1)
    if gear.get('cap'):
        col = g('cap')
        out += pth(f'M{cx - r * 1.0:.1f},{cy - r * .45:.1f} Q{cx - r * .95:.1f},{cy - r * 1.4:.1f} {cx + r * .05:.1f},{cy - r * 1.38:.1f} '
                   f'Q{cx + r:.1f},{cy - r * 1.32:.1f} {cx + r * 1.0:.1f},{cy - r * .45:.1f} Z', col, 1.2)
        out += pth(f'M{cx + r * .55:.1f},{cy - r * .52:.1f} Q{cx + r * 1.6:.1f},{cy - r * .66:.1f} {cx + r * 1.8:.1f},{cy - r * .38:.1f} '
                   f'Q{cx + r * 1.2:.1f},{cy - r * .24:.1f} {cx + r * .4:.1f},{cy - r * .38:.1f} Z', dark(col), 1.1)
        out += pth(f'M{cx:.1f},{cy - r * 1.37:.1f} Q{cx + r * .2:.1f},{cy - r * .9:.1f} {cx + r * .1:.1f},{cy - r * .47:.1f}', 'none', .7, dark(col, .6))
        out += circ(cx, cy - r * 1.38, r * .12, dark(col), .8)
    if gear.get('earmuffs'):
        col = g('earmuffs')
        out += pth(f'M{cx - r * 1.0:.1f},{cy - r * .1:.1f} Q{cx:.1f},{cy - r * 1.9:.1f} {cx + r * 1.0:.1f},{cy - r * .1:.1f}', 'none', r * .2, '#55524c')
        for sx in (-1, 1):
            out += curly(cx + sx * r * 1.0, cy, r * .34, r * .38, col, n=9, sw=1) + circ(cx + sx * r * 1.0 - r * .08, cy - r * .1, r * .1, '#fff', 0, opacity=.7)
    if gear.get('bow'):
        col = g('bow')
        bx, by, s = cx - r * .55, cy - r * .95, r * .3
        out += pth(f'M{bx:.1f},{by:.1f} L{bx - s * 1.6:.1f},{by - s:.1f} L{bx - s * 1.4:.1f},{by + s * 1.1:.1f} Z '
                   f'M{bx:.1f},{by:.1f} L{bx + s * 1.6:.1f},{by - s * 1.1:.1f} L{bx + s * 1.5:.1f},{by + s:.1f} Z', col, 1)
        out += circ(bx, by, s * .5, dark(col), 1)
    if gear.get('party'):
        col = g('party')
        x0, y0 = cx - r * .5, cy - r * .82
        out += pth(f'M{x0:.1f},{y0:.1f} L{cx + r * .2:.1f},{cy - r * 2.15:.1f} L{cx + r * .75:.1f},{cy - r * .7:.1f} Z', col, 1.1)
        out += pth(f'M{cx - r * .28:.1f},{cy - r * 1.18:.1f} L{cx + r * .62:.1f},{cy - r * 1.02:.1f} M{cx - r * .08:.1f},{cy - r * 1.6:.1f} L{cx + r * .45:.1f},{cy - r * 1.5:.1f}',
                   'none', r * .14, '#ffe08a')
        out += curly(cx + r * .2, cy - r * 2.2, r * .2, r * .2, '#ffe08a', n=7, sw=.9)
    if gear.get('crown'):
        y0, y1 = cy - r * .78, cy - r * 1.45
        pts = [(cx - r * .7, y0), (cx - r * .75, y1), (cx - r * .38, y0 - r * .32), (cx, y1 - r * .1), (cx + r * .38, y0 - r * .32), (cx + r * .75, y1), (cx + r * .7, y0)]
        out += pth('M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts) + ' Z', '#f5cf55', 1.1)
        out += circ(cx, y0 - r * .2, r * .1, '#e0457b', .7) + circ(cx - r * .45, y0 - r * .15, r * .07, '#3b6fb6', .6) + circ(cx + r * .45, y0 - r * .15, r * .07, '#3b6fb6', .6)
    if gear.get('glasses') or gear.get('shades'):
        ex, ey, sp, er = C.eyes
        lens = '#222' if gear.get('shades') else '#ffffff'
        op = .95 if gear.get('shades') else .2
        rr = er * 2.1
        for x in (ex - sp, ex + sp):
            out += circ(x, ey, rr, lens, 0, opacity=op) + circ(x, ey, rr, 'none', er * .4)
        out += pth(f'M{ex - sp + rr:.1f},{ey - er * .2:.1f} Q{ex:.1f},{ey - er * 1.0:.1f} {ex + sp - rr:.1f},{ey - er * .2:.1f}', 'none', er * .4)
        if gear.get('shades'):
            out += pth(f'M{ex - sp - rr * .5:.1f},{ey - rr * .3:.1f} l{rr * .5:.1f},{-rr * .3:.1f} M{ex + sp - rr * .5:.1f},{ey - rr * .3:.1f} l{rr * .5:.1f},{-rr * .3:.1f}', 'none', er * .3, '#fff')
    return out


# ---------------------------------------------------------------- held props (drawn at the paw, in character units)
def held(name, x, y, k, opt=None):
    """A prop in the near paw. Designed for a paw of radius 6, scaled by k."""
    c = opt if isinstance(opt, str) else None
    s = {
        'balloon': lambda: (pth('M0,0 C5,-14 -4,-28 3,-44', 'none', .8) + ell(3, -57, 11, 13, c or '#e0457b', 1.2) +
                            pth('M0,-44 L6,-44 L3,-47 Z', c or '#e0457b', 1) + ell(-1, -62, 3, 5, '#fff', 0, opacity=.6)),
        'book': lambda: (pth('M0,-4 L-13,-8 L-13,5 L0,9 Z', '#fffdf5', 1.1) + pth('M0,-4 L13,-8 L13,5 L0,9 Z', '#fffdf5', 1.1) +
                         pth('M-11,-4 L-2,-1 M-11,-1 L-2,2 M-11,2 L-2,5 M2,-1 L11,-4 M2,2 L11,-1 M2,5 L11,2', 'none', .5, '#9a948a') +
                         pth('M0,9 L-14,5 L-14,7 L0,11 L14,7 L14,5 Z', c or '#c9443b', 1)),
        'mug': lambda: (rct(-7, -16, 13, 15, c or '#3b6fb6', 1.2, rx=2) + pth('M6,-13 q6,0 6,5 q0,5 -6,5', 'none', 1.5) +
                        pth('M-3,-20 q-2,-3 0,-6 t0,-6 M2,-20 q-2,-3 0,-6 t0,-6', 'none', .8, '#9a9a9a') + ell(-.5, -16, 6.5, 1.6, '#6b3e1e', .8)),
        'umbrella': lambda: (pth('M0,6 L0,-40 M0,6 q0,5 4,5 q4,0 4,-4', 'none', 1.6) +
                             pth('M-28,-38 Q0,-66 28,-38 Q21,-43 14,-38 Q7,-43 0,-38 Q-7,-43 -14,-38 Q-21,-43 -28,-38 Z', c or '#e0457b', 1.2) +
                             pth('M0,-52 Q-7,-46 -14,-38 M0,-52 Q7,-46 14,-38', 'none', .7) + circ(0, -53, 1.6, INK, 0)),
        'flower': lambda: (pth('M0,4 Q2,-10 0,-22', 'none', 1.4, '#3f8a3a') + pth('M1,-8 q8,-6 11,-2 q-6,5 -11,2 Z', '#6cbf5a', .8) +
                           ''.join(circ(5.5 * math.cos(t), -26 + 5.5 * math.sin(t), 4, c or '#f6a6c6', .9) for t in [i * 2 * math.pi / 6 for i in range(6)]) +
                           circ(0, -26, 3.6, '#ffd84a', .9)),
        'icecream': lambda: (pth('M-7,-6 L7,-6 L0,13 Z', '#e7b36a', 1.1) + pth('M-4,-2 L3,6 M3,-4 L-2,4', 'none', .6, '#a8743a') +
                             circ(0, -12, 7.5, '#f6a6c6', 1.1) + circ(0, -22, 6.5, '#9ee0c8', 1.1) + circ(1, -29, 2, '#d33b2f', .8)),
        'wand': lambda: (pth('M0,6 L6,-22', 'none', 2.4, '#7a5a35') + star(7, -27, 8, '#ffd84a') + sparkle(17, -34, 3) + sparkle(-4, -36, 2.4)),
        'ball': lambda: soccer(0, -12, 9),
        'basketball': lambda: bball(0, -12, 9),
        'pizza': lambda: (pth('M-10,-20 Q0,-25 10,-20 L0,6 Z', '#f6d06b', 1.1) + pth('M-10,-20 Q0,-25 10,-20 Q0,-21 -10,-20 Z', '#c98a3c', 1.1) +
                          circ(-3, -13, 2.2, '#c9443b', .6) + circ(3, -10, 2, '#c9443b', .6) + circ(0, -3, 1.8, '#c9443b', .6)),
        'cookie': lambda: (circ(0, -8, 8, '#d9a35f', 1.1) + ''.join(circ(x, y, 1.2, '#5a3a1e', 0) for x, y in ((-3, -11), (3, -9), (-1, -5), (4, -4), (-4, -6)))),
        'rod': lambda: (pth('M-4,8 L44,-40', 'none', 2, '#7a5a35') + circ(3, 1, 3, '#888', .8) + pth('M44,-40 L46,10', 'none', .6)),
        'magnifier': lambda: (pth('M0,4 L10,-10', 'none', 3, '#7a5a35') + circ(15, -17, 8, '#dff1fb', 1.6) + pth('M10,-21 q3,-3 7,-2', 'none', 1, '#fff')),
        'rake': lambda: (pth('M-4,30 L14,-44', 'none', 2, '#a87b45') + pth('M4,-44 L24,-44 M6,-44 l-1,6 M10,-44 l-1,6 M14,-44 l-1,6 M18,-44 l-1,6 M22,-44 l-1,6', 'none', 1.3, '#666')),
        'flag': lambda: (pth('M0,6 L0,-40', 'none', 1.8, '#7a5a35') + pth('M0,-40 L24,-33 L0,-26 Z', c or '#2f5aa8', 1.1)),
        'leaf': lambda: leaf(4, -10, 9, c or '#e0782f'),
        'snowball': lambda: circ(0, -6, 6.5, '#ffffff', 1.1) + circ(-2, -8, 1.6, '#dce8f0', 0),
        'pumpkin': lambda: pumpkin(0, -1, 1.1),
        'fish': lambda: (pth('M0,0 L0,-6', 'none', .6) + fish(0, 4, 1, c)),
        'trophy': lambda: trophy(0, 0, 1),
        'gift': lambda: gift(0, 0, .9, c),
        'cocoa': lambda: (rct(-7, -16, 13, 15, c or '#c9443b', 1.2, rx=2) + pth('M6,-13 q6,0 6,5 q0,5 -6,5', 'none', 1.5) +
                          curly(-.5, -17, 6, 2.5, '#fff', n=7, sw=.8)),
    }.get(name)
    if not s:
        return ''
    return grp(s(), f'translate({x:.1f},{y:.1f}) scale({k:.2f})')


HELD = ['balloon', 'book', 'mug', 'cocoa', 'umbrella', 'flower', 'icecream', 'wand', 'ball', 'basketball', 'pizza', 'cookie',
        'rod', 'magnifier', 'rake', 'flag', 'leaf', 'snowball', 'pumpkin', 'fish', 'trophy', 'gift']


# ---------------------------------------------------------------- small shared drawings
def star(x, y, r, fill, sw=1):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * .45
        t = math.radians(-90 + 36 * i)
        pts.append(f'{x + rr * math.cos(t):.1f},{y + rr * math.sin(t):.1f}')
    return pth('M' + ' L'.join(pts) + ' Z', fill, sw)


def sparkle(x, y, r, color='#f5b82e'):
    return pth(f'M{x:.1f},{y - r:.1f} Q{x:.1f},{y:.1f} {x + r:.1f},{y:.1f} Q{x:.1f},{y:.1f} {x:.1f},{y + r:.1f} Q{x:.1f},{y:.1f} {x - r:.1f},{y:.1f} Q{x:.1f},{y:.1f} {x:.1f},{y - r:.1f} Z', color, 0)


def soccer(x, y, r):
    return (circ(x, y, r, '#fff', 1.2) + pth(f'M{x:.1f},{y - r * .35:.1f} l{r * .33:.1f},{r * .24:.1f} l{-r * .13:.1f},{r * .4:.1f} l{-r * .4:.1f},0 l{-r * .13:.1f},{-r * .4:.1f} Z', INK, 0) +
            pth(f'M{x:.1f},{y - r * .35:.1f} V{y - r:.1f} M{x + r * .33:.1f},{y - r * .11:.1f} L{x + r * .95:.1f},{y - r * .3:.1f} M{x + r * .2:.1f},{y + r * .29:.1f} L{x + r * .55:.1f},{y + r * .8:.1f} '
                f'M{x - r * .2:.1f},{y + r * .29:.1f} L{x - r * .55:.1f},{y + r * .8:.1f} M{x - r * .33:.1f},{y - r * .11:.1f} L{x - r * .95:.1f},{y - r * .3:.1f}', 'none', .7))


def bball(x, y, r):
    return (circ(x, y, r, '#e8823a', 1.2) + pth(f'M{x - r:.1f},{y:.1f} H{x + r:.1f} M{x:.1f},{y - r:.1f} V{y + r:.1f} '
                                                 f'M{x - r * .7:.1f},{y - r * .7:.1f} Q{x - r * .25:.1f},{y:.1f} {x - r * .7:.1f},{y + r * .7:.1f} '
                                                 f'M{x + r * .7:.1f},{y - r * .7:.1f} Q{x + r * .25:.1f},{y:.1f} {x + r * .7:.1f},{y + r * .7:.1f}', 'none', .8) +
            ell(x - r * .4, y - r * .45, r * .25, r * .15, '#fff', 0, opacity=.5))


def leaf(x, y, s, col):
    return (pth(f'M{x:.1f},{y + s:.1f} C{x - s:.1f},{y + s * .2:.1f} {x - s * .8:.1f},{y - s * .7:.1f} {x:.1f},{y - s:.1f} '
                f'C{x + s * .8:.1f},{y - s * .7:.1f} {x + s:.1f},{y + s * .2:.1f} {x:.1f},{y + s:.1f} Z', col, .9) +
            pth(f'M{x:.1f},{y + s * 1.3:.1f} L{x:.1f},{y - s * .6:.1f} M{x:.1f},{y:.1f} l{s * .4:.1f},{-s * .35:.1f} M{x:.1f},{y + s * .35:.1f} l{-s * .4:.1f},{-s * .35:.1f}', 'none', .6, dark(col, .6)))


def pumpkin(x, y, s, col='#e8823a'):
    """Base center (x, y)."""
    r = 9 * s
    cy = y - r * .85
    return (pth(f'M{x:.1f},{cy - r * .7:.1f} q{-1 * s:.1f},{-4 * s:.1f} {2 * s:.1f},{-6 * s:.1f}', 'none', 2.2 * s, '#5f7f2c') +
            ell(x - r * .55, cy, r * .6, r * .85, col, 1.1) + ell(x + r * .55, cy, r * .6, r * .85, col, 1.1) + ell(x, cy, r * .62, r * .9, col, 1.1) +
            pth(f'M{x + 2 * s:.1f},{cy - r * .78:.1f} q{5 * s:.1f},{-4 * s:.1f} {8 * s:.1f},{-1 * s:.1f}', 'none', .8, '#5f7f2c') +
            ell(x - r * .25, cy - r * .35, r * .15, r * .3, '#fff', 0, opacity=.35))


def fish(x, y, s, col=None):
    col = col or '#7fb3d5'
    return grp(pth('M0,0 C6,-4 6,14 0,18 C-6,14 -6,-4 0,0 Z', col, 1) + pth('M0,17 L-5,23 L5,23 Z', col, 1) + circ(-1.5, 4, 1.1, INK, 0) +
               pth('M-3,8 q3,2 6,0 M-3,11 q3,2 6,0', 'none', .5, dark(col)), f'translate({x:.1f},{y:.1f}) scale({s})')


def trophy(x, y, s):
    return grp(pth('M-8,-30 H8 Q8,-16 0,-14 Q-8,-16 -8,-30 Z', '#f5cf55', 1.1) + pth('M-8,-27 q-6,0 -5,5 q1,4 6,3 M8,-27 q6,0 5,5 q-1,4 -6,3', 'none', 1.2) +
               rct(-1.5, -14, 3, 7, '#d9a520', .9) + rct(-6, -7, 12, 4, '#7a5a35', 1) + star(0, -23, 3.2, '#fff6c8', .5),
               f'translate({x:.1f},{y:.1f}) scale({s})')


def gift(x, y, s, col=None):
    col = col or '#3b6fb6'
    return grp(rct(-9, -16, 18, 15, col, 1.1) + rct(-10, -19, 20, 4, dark(col, .85), 1.1) + rct(-1.6, -19, 3.2, 18, '#ffd84a', .7) +
               pth('M0,-19 q-8,-8 -8,-2 q0,3 8,2 q8,1 8,-2 q0,-6 -8,2 Z', '#ffd84a', .8), f'translate({x:.1f},{y:.1f}) scale({s})')


# ---------------------------------------------------------------- the cast
class Char:
    key = name = ''
    scale = .66
    lash = False
    blush = '#f2a7a0'
    lw = 1.1
    hand_r = 6
    sit_drop = 0

    def back(self, P): return ''
    def body(self): return ''
    def head_back(self): return ''
    def head_front(self, face): return ''
    def hand(self, x, y, ang): return ''
    def foot(self, x, y, side): return ''
    def sit_feet(self): return ''

    def leg(self, side, a, b):
        hx, hy = side * self.hip[0], self.hip[1]
        E, F = fk((hx, hy), side, a, b, *self.leg_len)
        return limb([(hx, hy), E, F], self.leg_w, self.leg_fill) + self.foot(F[0], F[1], side)

    def arm(self, side, spec):
        S = (side * self.shoulder[0], self.shoulder[1])
        L1, L2 = self.arm_len
        if isinstance(spec, str):
            T = self.targets[spec]
            if spec == 'hip':
                T = (side * T[0], T[1])
            E, Hd = ik(S, T, L1, L2, side)
        else:
            E, Hd = fk(S, side, spec[0], spec[1], L1, L2)
        ang = math.degrees(math.atan2(Hd[1] - E[1], Hd[0] - E[0])) - 90
        return limb([S, E], self.arm_w, self.arm_fill) + limb([E, Hd], self.arm_w * .95, self.fore_fill) + self.hand(Hd[0], Hd[1], ang), Hd

    @property
    def fore_fill(self): return self.arm_fill

    @property
    def top(self): return self.head[1] - self.head[2] * 1.25


class Bear(Char):
    key, name, scale = 'bear', 'Big Bear', .66
    FUR, SH, IN, PAD = '#fbfaf3', '#e2dccb', '#f2ecdb', '#3d3833'
    shoulder, hip = (21, -62), (12, -24)
    arm_len, arm_w, leg_len, leg_w = (14, 13), 12, (11, 8), 14
    arm_fill = leg_fill = FUR
    neck, head = (4, -67, 36), (4, -84, 22)
    eyes, mouth = (5, -89, 8.5, 2.7), (9, -72.5, 10)
    cheeks = [(-7, -79, 3.6), (21, -79, 3.6)]
    lid = FUR
    lw = 1.2
    hand_r = 6.5
    sit_drop = 19
    targets = {'chin': (9, -66), 'face': (10, -86), 'belly': (4, -42), 'hip': (21, -44)}

    def body(self):
        return (ell(0, -44, 27, 28, self.FUR) + ell(3, -40, 16, 18, self.IN, 0) + crescent(0, -44, 27, 28, self.SH) + ell(0, -44, 27, 28, 'none') +
                tufts([(-14, -55, 2.2), (-17, -36, 2), (14, -24, 2), (-6, -22, 1.8)], self.SH, .9))

    def head_back(self):
        return ''.join(circ(x, -100, 7.5, self.FUR) + circ(x + .5, -99.5, 4, self.SH, 0) for x in (-12, 19))

    def head_front(self, face):
        F = self.FUR
        out = (pth('M-17.5,-81 L-22.5,-77 L-17.5,-76 L-21,-71.5 L-15,-72', F, 1.2) + pth('M25.5,-81 L30.5,-77 L25.5,-76 L29,-71.5 L23,-72', F, 1.2) +
               ell(4, -84, 23, 20, F) + crescent(4, -84, 23, 20, self.SH, t1=-30, t2=120, depth=.25) + ell(4, -84, 23, 20, 'none') +
               pth('M-1,-103 Q1,-109 3,-103.5 Q6,-108.5 7.5,-102.5', 'none', 1.1) +
               ell(9, -77, 11.5, 8.5, self.IN, 1) +
               pth('M3,-82.5 Q9,-86 15,-82.5 Q15,-79 9,-77.5 Q3,-79 3,-82.5 Z', INK, 0) + ell(7, -83, 2, 1, '#fff', 0, opacity=.8) +
               pth('M9,-77.5 V-74.5', 'none', 1.1))
        return out + draw_face(self, face)

    def hand(self, x, y, ang):
        return grp(circ(0, 0, 6.5, self.FUR, 1.3) + pth('M-2.6,3.6 l-.6,2.4 M0,4.4 v2.4 M2.6,3.6 l.6,2.4', 'none', .9) +
                   crescent(0, 0, 6.5, 6.5, self.SH, t1=-20, t2=110, depth=.3), f'translate({x:.1f},{y:.1f}) rotate({ang:.0f})')

    def foot(self, x, y, side):
        return ell(x + side * 2, y, 10, 5, self.FUR, 1.3) + pth(f'M{x + side * 2 + 5:.1f},{y - 3.5:.1f} l1,2 M{x + side * 2 + 1:.1f},{y - 4.5:.1f} l.5,2 M{x + side * 2 - 3:.1f},{y - 4.6:.1f} l0,2', 'none', .8)

    def sit_feet(self):
        out = ''
        for sx in (-1, 1):
            x, y = sx * 15, -7
            out += (ell(x, y, 9, 7.5, self.FUR, 1.3) + ell(x, y + 1.5, 4.2, 3.2, self.PAD, 0) +
                    ''.join(circ(x + dx, y - 4, 1.6, self.PAD, 0) for dx in (-4.5, 0, 4.5)))
        return out


class Fox(Char):
    key, name, scale = 'fox', 'Artic', .68
    FUR, SH, DEEP, SOCK, EAR = '#fdfdfb', '#d3dce6', '#a7b4c2', '#7d8a99', '#ecc9cd'
    shoulder, hip = (11, -43), (7, -18)
    arm_len, arm_w, leg_len, leg_w = (9, 8), 6.5, (8, 7), 7.5
    arm_fill = leg_fill = FUR
    neck, head = (2, -49, 22), (2, -63, 17)
    eyes, mouth = (3, -65, 6.5, 2.3), (9, -53.5, 7)
    cheeks = [(-7, -57, 2.6), (16, -57, 2.6)]
    lid = FUR
    hand_r = 4.2
    sit_drop = 13
    targets = {'chin': (7, -49), 'face': (8, -62), 'belly': (2, -32), 'hip': (12, -31)}

    def back(self, P):
        ang = {'cheer': -18, 'run': 18, 'dance': -25, 'scared': 10, 'wave': -8}.get(P.get('_name'), 0)
        t = (pth('M-6,-22 C-26,-20 -40,-30 -40,-48 C-40,-58 -33,-66 -26,-65 L-29,-60 L-24,-61 L-27,-56 L-22,-57 '
                 'C-26,-46 -22,-34 -6,-30 Z', self.FUR, 1.3) +
             pth('M-32,-40 C-34,-48 -32,-55 -27,-59 C-30,-50 -28,-42 -20,-35 Z', self.SH, 0) +
             tufts([(-36, -46, 1.8), (-30, -34, 1.6)], self.DEEP, .8))
        return grp(t, f'rotate({ang} -6 -26)')

    def body(self):
        return (ell(0, -32, 14, 17, self.FUR) + crescent(0, -32, 14, 17, self.SH) + ell(0, -32, 14, 17, 'none') +
                pth('M-9,-46 Q1,-50 10,-46 L8,-37 L5.5,-39.5 L3.5,-34 L1,-38 L-1.5,-33 L-4,-38.5 L-7,-35 Z', '#ffffff', .8))

    def head_back(self):
        return (pth('M-11,-70 L-15,-91 L-1,-75 Z', self.FUR, 1.3) + pth('M-10,-72 L-13,-86 L-4,-75 Z', self.EAR, 0) +
                pth('M7,-75 L18,-91 L18,-68 Z', self.FUR, 1.3) + pth('M9,-74 L16.5,-86 L16.5,-70 Z', self.EAR, 0))

    def head_front(self, face):
        d = ('M2,-76 C12,-76 18,-71 19,-64 L23.5,-60 L18.5,-59 L21,-54.5 L14.5,-54.5 C11,-50 7,-48 5,-48 C1,-48 -5,-51 -9,-54.5 '
             'L-15,-54.5 L-12.5,-57.5 L-17.5,-60 L-14,-63 C-14,-71 -8,-76 2,-76 Z')
        out = (pth(d, self.FUR, 1.3) + crescent(2, -63, 16, 13, self.SH, t1=-20, t2=110, depth=.2) +
               pth('M-4,-73 Q-1,-77 2,-73 M2,-74 Q5,-78 8,-74', 'none', .7, self.DEEP) +
               ell(8, -55.5, 6.5, 4.5, '#ffffff', 0) +
               ell(9.5, -58.5, 2.7, 2, INK, 0) + ell(8.7, -59.1, .9, .5, '#fff', 0) + pth('M9.5,-56.5 V-54.3', 'none', .9))
        return out + draw_face(self, face)

    def hand(self, x, y, ang):
        return grp(circ(0, 0, 4.2, self.SOCK, 1.2) + pth('M-1.5,2.4 v1.6 M1.5,2.4 v1.6', 'none', .7), f'translate({x:.1f},{y:.1f}) rotate({ang:.0f})')

    def foot(self, x, y, side):
        return ell(x + side * 1.5, y, 6, 3.4, self.SOCK, 1.2) + pth(f'M{x + side * 1.5 + 2:.1f},{y - 2:.1f} v1.6 M{x + side * 1.5 - 1:.1f},{y - 2.6:.1f} v1.6', 'none', .6)

    def sit_feet(self):
        return ''.join(ell(sx * 9, -4, 5.2, 4.2, self.SOCK, 1.2) + ell(sx * 9, -3.4, 2.2, 1.6, '#4f5966', 0) +
                       ''.join(circ(sx * 9 + dx, -6.6, .9, '#4f5966', 0) for dx in (-2.4, 0, 2.4)) for sx in (-1, 1))


class Poodle(Char):
    key, name, scale = 'mack', 'Mackenzie', .74
    FUR, SH, DEEP, LIGHT = '#e3ad74', '#c48d55', '#9a6533', '#f2d1a3'     # apricot
    shoulder, hip = (9, -31), (6, -14)
    arm_len, arm_w, leg_len, leg_w = (6, 6), 6.5, (6, 5), 7
    arm_fill = leg_fill = FUR
    neck, head = (2, -35, 18), (2, -46, 12.5)
    eyes, mouth = (3, -48.3, 5.6, 2.1), (6.5, -37.6, 6)
    cheeks = []
    lid = FUR
    lw = 1
    hand_r = 3.8
    sit_drop = 10
    targets = {'chin': (6, -36), 'face': (6, -45), 'belly': (1, -23), 'hip': (10, -24)}

    def back(self, P):
        wag = {'cheer': -20, 'run': 10, 'dance': -15, 'wave': -10}.get(P.get('_name'), 0)
        return grp(pth('M-8,-26 Q-14,-30 -15,-36', 'none', 3.6, INK) + pth('M-8,-26 Q-14,-30 -15,-36', 'none', 1.6, self.FUR) +
                   curly(-16, -40, 5.5, 5.5, self.FUR, n=9) + curls([(-17, -41, 1.3)], self.SH), f'rotate({wag} -8 -26)')

    def body(self):
        return (curly(0, -24, 13, 12, self.FUR) + crescent(0, -24, 12, 11, self.SH, depth=.3, op=.7) +
                curls([(-6, -27, 1.4), (4, -19, 1.4), (-2, -16, 1.2), (7, -28, 1.2)], self.SH))

    def head_back(self):
        return ''

    def head_front(self, face):
        out = (curly(2, -46, 12, 11, self.FUR) + crescent(2, -46, 11, 10, self.SH, op=.6) +
               curls([(-4, -53, 1.3), (3, -55, 1.3), (8, -52, 1.1)], self.SH) +
               pth('M-5,-55 q-3,-2 -2,-5 M1,-57 q0,-3 3,-4 M7,-56 q3,-1 4,-4', 'none', 1, self.DEEP))           # scruffy tufts, no topknot
        out += draw_face(self, face, with_mouth=False)
        out += (curly(6.5, -40.5, 7, 4.6, self.LIGHT, n=9, sw=1) +
                ell(6.5, -42.8, 2.6, 2, INK, 0) + ell(5.9, -43.4, .8, .5, '#fff', 0))
        out += mouth(FACES.get(face, FACES['happy'])[1], *self.mouth, self.lw)
        out += pth('M-4.5,-53.5 q2,-2.5 4,-.5 M5,-53.5 q2,-2.5 4.5,-.5', 'none', 1, self.DEEP)
        for x in (-11.5, 15.5):
            out += curly(x, -41, 5, 9.5, self.FUR, n=10) + curls([(x - 1, -43, 1.2), (x + .5, -37, 1.1)], self.SH)
        return out

    def hand(self, x, y, ang):
        return curly(x, y, 3.8, 3.8, self.FUR, n=7, sw=1)

    def foot(self, x, y, side):
        return curly(x + side, y - .5, 4.6, 3.6, self.FUR, n=8, sw=1)

    def sit_feet(self):
        return ''.join(curly(sx * 7, -4, 4.6, 4, self.FUR, n=8, sw=1) for sx in (-1, 1))


class Unicorn(Char):
    key, name, scale = 'uni', 'Uni', .62
    BODY, SH, DEEP, HOOF, MUZ = '#fbf8ff', '#e3dbf3', '#c9bce7', '#a98bd8', '#fbf3fb'
    MANE = ['#f6a6c6', '#c4a3ef', '#8fd3e6', '#ffe08a']
    shoulder, hip = (13, -53), (9, -22)
    arm_len, arm_w, leg_len, leg_w = (10, 10), 8, (10, 8), 9.5
    arm_fill = leg_fill = BODY
    neck, head = (1, -57, 22), (1, -73, 15)
    eyes, mouth = (1, -75, 6.6, 3.0), (10, -58, 7)
    cheeks = [(-8, -67, 3), (14, -70, 2.6)]
    lid = BODY
    lash = True
    hand_r = 4.5
    sit_drop = 16
    targets = {'chin': (8, -55), 'face': (4, -73), 'belly': (2, -38), 'hip': (16, -39)}

    def back(self, P):
        flick = {'cheer': -15, 'run': 15, 'dance': -20}.get(P.get('_name'), 0)
        t = ''.join(pth(f'M-12,-{30 - i * 3} C-26,-{30 - i * 2} -30,-{14 + i * 2} -40,-{18 - i * 3} C-34,-{8 + i} -22,-{12 + i} -10,-{24 - i * 2} Z', c, 1.1)
                    for i, c in enumerate(self.MANE[:3]))
        return grp(t, f'rotate({flick} -12 -28)')

    def body(self):
        return (ell(0, -40, 18, 21, self.BODY) + ell(3, -36, 10, 12, '#ffffff', 0) + crescent(0, -40, 18, 21, self.SH) + ell(0, -40, 18, 21, 'none'))

    def head_back(self):
        out = ''
        locks = [('M-6,-86 C-20,-86 -24,-70 -18,-60 C-15,-54 -19,-48 -24,-44 C-12,-45 -9,-54 -9,-64 Z', 0),
                 ('M-9,-80 C-22,-76 -22,-62 -16,-55 C-12,-50 -14,-44 -17,-40 C-7,-43 -5,-52 -7,-62 Z', 1),
                 ('M-10,-70 C-18,-62 -14,-54 -10,-50 C-7,-47 -8,-43 -10,-39 C-3,-42 -2,-50 -4,-58 Z', 2)]
        for d, i in locks:
            out += pth(d, self.MANE[i], 1.1)
        out += (pth('M-8,-82 Q-14,-95 -6,-98 Q-2,-90 -3,-83 Z', self.BODY, 1.2) + pth('M-7,-84 Q-11,-93 -6,-95 Q-4,-90 -4.5,-85 Z', '#f6c3d6', 0) +
                pth('M6,-85 Q8,-97 15,-96 Q14,-88 11,-82 Z', self.BODY, 1.2) + pth('M7.5,-85 Q9,-94 13.5,-94 Q12.5,-88 10.5,-84 Z', '#f6c3d6', 0))
        out += (pth('M-2.5,-86 L3,-109 L7.5,-86 Z', '#f5cf55', 1.1) +
                pth('M-1.8,-90 L6.6,-92 M-.6,-95 L5.6,-97 M.6,-100 L4.6,-101.5 M1.6,-104.5 L3.8,-105.5', 'none', .9, '#d9a520') +
                pth('M.5,-88 L3,-104', 'none', .7, '#fff6c8'))
        return out

    def head_front(self, face):
        cr = circ(1, -73, 14.5, self.BODY)
        mz = ell(9, -62, 11, 8.5, self.MUZ)
        out = (cr + mz + circ(1, -73, 14.5, self.BODY, 0) + ell(9, -62, 11, 8.5, self.MUZ, 0) +
               crescent(9, -62, 11, 8.5, self.SH, t1=-10, t2=120, depth=.2) +
               pth('M13.5,-77 A14.5,14.5 0 0 1 15.4,-71', 'none', 1.3) +
               pth('M-13.4,-68 A14.5,14.5 0 0 1 -5,-86.5', 'none', 1.3) +
               pth('M-13.4,-68 Q-11,-60 -1,-57 Q6,-53 14,-55 Q20,-58 20,-63 Q20,-70 15.4,-71', 'none', 1.3) +
               ell(6, -63.5, 1.3, 1.9, self.DEEP, 0) + ell(13, -64, 1.3, 1.9, self.DEEP, 0))
        out += draw_face(self, face)
        out += (pth('M-6,-86 C-2,-90 6,-90 9,-84 C5,-86 2,-84 1,-80 C-1,-84 -4,-85 -6,-86 Z', self.MANE[3], 1) +
                pth('M-3,-87 C0,-92 6,-91 7,-87 C4,-88 2,-87 0,-84 Z', self.MANE[0], .9))
        return out

    def hand(self, x, y, ang):
        return grp(rct(-4.6, -1.5, 9.2, 7, self.HOOF, 1.2, rx=2.6) + pth('M-3.6,3.2 H3.6', 'none', .6, dark(self.HOOF)), f'translate({x:.1f},{y:.1f}) rotate({ang:.0f})')

    def foot(self, x, y, side):
        return pth(f'M{x - 5.5:.1f},{y + 2.5:.1f} L{x - 4.5:.1f},{y - 3.5:.1f} L{x + 4.5:.1f},{y - 3.5:.1f} L{x + 5.5:.1f},{y + 2.5:.1f} Z', self.HOOF, 1.2) + \
            pth(f'M{x - 4.6:.1f},{y - 1:.1f} H{x + 4.6:.1f}', 'none', .6, dark(self.HOOF))

    def sit_feet(self):
        return ''.join(ell(sx * 10, -5, 6.2, 4.8, self.HOOF, 1.2) + ell(sx * 10, -4.6, 3.6, 2.6, dark(self.HOOF, .8), 0) for sx in (-1, 1))


class Bob(Char):
    key, name, scale = 'bob', 'Bob', .84
    SKIN, SKSH, SHIRT, PANTS = '#f6cd3b', '#d9aa1e', '#d33b2f', '#2f5aa8'
    shoulder, hip = (9.5, -38.5), (5, -19)
    arm_len, arm_w, leg_len, leg_w = (7, 7), 5.6, (9, 9), 9
    neck, head = (0, -42.5, 17), (0, -52, 10)
    eyes, mouth = (1.6, -53.5, 3.9, 1.55), (1.8, -48.8, 7.5)
    cheeks = []
    lid = SKIN
    lw = .9
    hand_r = 3.4
    sit_drop = 14
    targets = {'chin': (3, -45), 'face': (4, -52), 'belly': (0, -30), 'hip': (10, -29)}

    @property
    def arm_fill(self): return self.shirt

    @property
    def fore_fill(self): return self.shirt

    shirt = SHIRT

    def leg(self, side, a, b):
        hx, hy = side * self.hip[0], self.hip[1]
        return grp(rct(-4.6, 0, 9.2, 15.5, self.PANTS, 1.2) + rct(-4.6, 14, 9.2 + 2.5, 4.5, self.PANTS, 1.2, rx=.8) +
                   pth('M2.6,1 V13.5', 'none', .7, dark(self.PANTS, .7)),
                   f'translate({hx:.1f},{hy - 1:.1f}) rotate({-a * side * .8:.0f})')

    def body(self):
        s = self.shirt
        return (rct(-11, -22.5, 22, 5, self.PANTS, 1.2, rx=.8) +
                pth('M-8.5,-41 L8.5,-41 L11.5,-21.5 L-11.5,-21.5 Z', s, 1.3) +
                pth('M5,-41 L8.5,-41 L11.5,-21.5 L7.5,-21.5 Z', dark(s, .85), 0) +
                pth('M-8.5,-41 L8.5,-41 L11.5,-21.5 L-11.5,-21.5 Z', 'none', 1.3) +
                pth('M-3.5,-41 L0,-35.5 L3.5,-41', 'none', 1) + circ(0, -31, .9, '#fff', 0) + circ(0, -27, .9, '#fff', 0) +
                rct(-3.4, -44, 6.8, 3.6, self.SKIN, 1))

    def head_front(self, face):
        out = (rct(-5, -64.5, 10, 4.8, self.SKIN, 1.1, rx=1.2) + ell(0, -64.5, 5, 1.3, self.SKIN, 1) +
               rct(-9.5, -61, 19, 18, self.SKIN, 1.3, rx=4.2) +
               rct(4.5, -60.3, 4.3, 16.6, self.SKSH, 0, rx=2.2) + rct(-8, -59, 2.4, 13, '#fff1b0', 0, rx=1.2) +
               rct(-9.5, -61, 19, 18, 'none', 1.3, rx=4.2))
        return out + draw_face(self, face)

    def hand(self, x, y, ang):
        return grp(circ(0, 1, 3.4, self.SKIN, 1.1) + pth('M-1.6,3.2 Q0,1.6 1.6,3.2', 'none', 1.2, dark(self.SKIN, .7)) +
                   rct(-2, -2.4, 4, 2.4, self.SKIN, 0), f'translate({x:.1f},{y:.1f}) rotate({ang:.0f})')

    def sit_feet(self):
        return ''.join(rct(sx * 5 - 4.6, -9, 9.2, 8.5, self.PANTS, 1.2, rx=.8) + rct(sx * 5 - 3.6, -3.4, 7.2, 2, dark(self.PANTS, .65), 0) for sx in (-1, 1))


CAST = {c.key: c for c in (Bear(), Fox(), Poodle(), Unicorn(), Bob())}
ALIASES = {'big bear': 'bear', 'bigbear': 'bear', 'polar bear': 'bear', 'artic': 'fox', 'arctic fox': 'fox',
           'mackenzie': 'mack', 'poodle': 'mack', 'unicorn': 'uni', 'lego': 'bob', 'brick': 'bob'}


def who(name):
    k = str(name).strip().lower()
    k = ALIASES.get(k, k)
    if k not in CAST:
        raise SystemExit(f"comic: unknown character '{name}' (cast: {', '.join(CAST)})")
    return CAST[k]


def figure(C, pose='stand', face='happy', gear=None, hold=None, hold_opt=None, shirt=None, flip=False):
    """One character in local units: origin at the feet, facing right (flip: the caller mirrors it; text is kept readable)."""
    C._flip = flip
    if pose not in POSES:
        raise SystemExit(f"comic: unknown pose '{pose}' (poses: {', '.join(POSES)})")
    if face not in FACES:
        raise SystemExit(f"comic: unknown face '{face}' (faces: {', '.join(FACES)})")
    gear = dict(gear or {})
    if C.key == 'mack' and 'collar' not in gear:
        gear['collar'] = True                      # Mackenzie's own lavender collar and tag; set "collar": false to drop it
    if C.key == 'bob':
        C.shirt = shirt or Bob.SHIRT
    P = dict(POSES[pose], _name=pose)
    sit = P.get('sit')
    dy = C.sit_drop if sit else P.get('dy', 0)
    legs = '' if sit else C.leg(-1, *P['LL']) + C.leg(1, *P['RL'])
    far, _ = C.arm(-1, P['L'])
    near, hand = C.arm(1, P['R'])
    hx, hy = C.neck[0], C.neck[1]
    headg = grp(C.head_back() + C.head_front(face) + gear_head(C, gear), f'rotate({P.get("tilt", 0)} {hx} {hy})')
    prop = held(hold, hand[0], hand[1], max(.85, C.hand_r / 6), hold_opt) if hold else ''
    if hold and not prop:
        raise SystemExit(f"comic: unknown held prop '{hold}' (held: {', '.join(HELD)})")
    feet = grp(C.sit_feet(), f'translate(0,{-dy})') if sit else ''
    upper = C.back(P) + gear_back(C, gear) + C.body() + feet + gear_neck(C, gear) + far + headg + prop + near
    fx = motion(P.get('fx'), C, hand)
    lean = P.get('lean', 0)
    return grp(grp(legs, f'translate(0,{dy})') + grp(upper + fx, f'translate(0,{dy}) rotate({lean} 0 {C.hip[1]})'))


def motion(kind, C, hand):
    if not kind:
        return ''
    x, y = hand
    if kind == 'wave':
        return pth(f'M{x + 7:.1f},{y - 6:.1f} q4,4 0,9 M{x + 10:.1f},{y - 9:.1f} q6,7 0,14 M{x - 8:.1f},{y - 6:.1f} q-4,4 0,9', 'none', 1)
    if kind == 'jump':
        return pth('M-14,12 h-6 M-6,15 h-7 M8,15 h7 M16,12 h6', 'none', 1)
    if kind == 'speed':
        top, mid = C.top, (C.top + 0) / 2
        return pth(f'M-26,{mid - 8:.0f} h-12 M-30,{mid:.0f} h-14 M-26,{mid + 8:.0f} h-10', 'none', 1) + curly(-24, -3, 5, 3, '#ffffff', n=7, sw=.8, stroke='#9a948a')
    if kind == 'notes':
        cx, cy, r = C.head
        return ''.join(pth(f'M{cx + r * a:.1f},{cy - r * b:.1f} v-7 l5,-2 v7', 'none', 1) + ell(cx + r * a - 1.5, cy - r * b, 2, 1.5, INK, 0) +
                       ell(cx + r * a + 3.5, cy - r * b - 2, 2, 1.5, INK, 0) for a, b in ((1.3, .9), (-1.5, 1.2)))
    if kind == 'shake':
        cx, cy, r = C.head
        return pth(f'M{cx - r * 1.35:.1f},{cy - r * .4:.1f} q-3,3 0,6 M{cx + r * 1.35:.1f},{cy - r * .4:.1f} q3,3 0,6 M{cx - r * 1.6:.1f},{cy - r * .6:.1f} q-3,4 0,9 M{cx + r * 1.6:.1f},{cy - r * .6:.1f} q3,4 0,9', 'none', 1)
    if kind == 'think':
        return ''
    return ''


# ---------------------------------------------------------------- scenes (panel backgrounds)
def _frame(inner, bg):
    return rct(1, 1, W - 2, H - 2, bg, 0) + inner


def trees_far(xs, y, col='#9cc48a'):
    return ''.join(curly(x, y - 10, 11, 9, col, n=9, sw=.9) for x in xs)


def pine(x, y, s=1, col='#3f7a52', snow=False):
    out = rct(x - 1.5 * s, y - 5 * s, 3 * s, 5 * s, '#7a5a35', .8)
    for i, (w, h) in enumerate(((10, 10), (8, 9), (6, 8))):
        by = y - 4 * s - i * 7 * s
        out += pth(f'M{x - w * s:.1f},{by:.1f} L{x:.1f},{by - h * s - 4 * s:.1f} L{x + w * s:.1f},{by:.1f} Z', col, .9)
        if snow:
            out += pth(f'M{x - w * s * .5:.1f},{by - h * s * .55:.1f} L{x:.1f},{by - h * s - 4 * s:.1f} L{x + w * s * .5:.1f},{by - h * s * .55:.1f} Q{x:.1f},{by - h * s * .35:.1f} {x - w * s * .5:.1f},{by - h * s * .55:.1f} Z', '#fff', 0)
    return out


def tree(x, y, s=1, col='#e0782f'):
    return (pth(f'M{x - 2.5 * s:.1f},{y:.1f} L{x - 2 * s:.1f},{y - 22 * s:.1f} L{x + 2 * s:.1f},{y - 22 * s:.1f} L{x + 2.5 * s:.1f},{y:.1f} Z', '#7a5a35', 1) +
            curly(x, y - 32 * s, 15 * s, 13 * s, col, sw=1) + curly(x - 8 * s, y - 25 * s, 8 * s, 7 * s, dark(col, .9), sw=.9) +
            curly(x + 6 * s, y - 40 * s, 7 * s, 6 * s, col, sw=.9))


def cloud(x, y, s=1):
    return curly(x, y, 14 * s, 6 * s, '#ffffff', n=10, sw=.9)


def scene(name, sky=None):
    """Returns (background svg, ground y)."""
    g = 104
    if name == 'snow':
        bg = sky or '#d9e8f4'
        out = (pth('M0,86 Q40,70 90,82 T200,76 V122 H0 Z', '#eef4f9', 1) + pine(26, 84, .8, snow=True) + pine(170, 80, .9, snow=True) + pine(184, 82, .7, snow=True) +
               pth('M0,100 Q60,94 120,99 T200,97 V122 H0 Z', '#fbfdff', 1) +
               ''.join(circ(x, y, 1.4, '#fff', .5, '#9fb7c9') for x, y in ((14, 18), (48, 40), (96, 14), (140, 34), (178, 16), (66, 64), (122, 58), (190, 54))))
    elif name == 'ice':
        bg = sky or '#fbe0bf'
        g = 100
        out = (circ(172, 82, 14, '#f6b25c', 0, opacity=.85) + pth('M1,90 L199,90 L199,121 L1,121 Z', '#cfe3ef', 1) +
               pth('M10,100 L40,96 M150,108 L190,104 M70,114 L100,111', 'none', 1, '#9fbfd2'))
    elif name == 'autumn':
        bg = sky or '#f6ead2'
        out = (tree(18, 98, 1.0, '#e0782f') + tree(182, 96, 1.1, '#d9a520') + tree(150, 94, .7, '#c9443b') +
               pth('M0,98 Q70,92 130,97 T200,95 V122 H0 Z', '#d9bb7e', 1) +
               pth('M20,108 l2,-3 M60,112 l2,-3 M110,106 l2,-3 M160,113 l2,-3', 'none', .8, '#a8874d') +
               leaf(62, 22, 3, '#e0782f') + leaf(110, 40, 3, '#d9a520') + leaf(140, 16, 3, '#c9443b') + leaf(88, 60, 2.6, '#e0782f'))
    elif name == 'hill':
        bg = sky or '#d6ebf7'
        out = (cloud(40, 20) + cloud(150, 30, .8) + pth('M0,100 Q60,80 120,92 T200,88 V122 H0 Z', '#a8d58a', 1) +
               pth('M0,106 Q80,98 200,104 V122 H0 Z', '#94c776', 0) + tufts([(30, 104, 1.5), (90, 108, 1.5), (150, 104, 1.5), (180, 112, 1.5)], '#5f9a46'))
    elif name == 'beach':
        bg = sky or '#cfe9f6'
        g = 106
        out = (circ(166, 22, 11, '#ffd84a', 1) + pth('M1,78 H199 V96 H1 Z', '#6fb7d8', 1) +
               pth('M14,84 q5,-3 10,0 M60,88 q5,-3 10,0 M120,83 q5,-3 10,0 M164,89 q5,-3 10,0', 'none', .8, '#fff') +
               pth('M0,96 Q100,90 200,96 V122 H0 Z', '#f1dca6', 1) + pth('M40,18 q3,-3 6,0 q3,-3 6,0 M70,30 q2,-2 4,0 q2,-2 4,0', 'none', .9))
    elif name == 'night':
        bg = sky or '#22385f'
        out = (pth('M168,14 a10,10 0 1 0 10,14 a8,8 0 1 1 -10,-14 Z', '#fff4c4', .8) +
               ''.join(star(x, y, 2.2, '#ffe08a', 0) for x, y in ((20, 16), (60, 30), (100, 12), (130, 34), (40, 52), (190, 50))) +
               pth('M0,98 Q70,88 130,96 T200,92 V122 H0 Z', '#3d5a3a', 1))
    elif name == 'kitchen':
        bg = sky or '#f7e7c4'
        g = 108
        out = (''.join(pth(f'M1,{y} H199', 'none', .5, '#d9c49a') for y in range(54, 100, 9)) +
               rct(120, 12, 50, 34, '#cfe9f6', 1.4) + pth('M145,12 V46 M120,29 H170', 'none', 1.2) +
               pth('M116,10 Q122,30 118,48 L114,48 L114,10 Z M174,10 Q168,30 172,48 L176,48 L176,10 Z', '#e0457b', 1) +
               rct(8, 62, 50, 36, '#c98f55', 1.2) + rct(5, 58, 56, 5, '#e9e2d0', 1.2) + circ(22, 80, 1.3, INK, 0) + circ(44, 80, 1.3, INK, 0) +
               pth('M1,100 H199 V121 H1 Z', '#c99a64', 1) + pth('M30,100 V121 M80,100 V121 M130,100 V121 M175,100 V121', 'none', .6, '#9a7044'))
    elif name == 'living':
        bg = sky or '#e9e0ef'
        g = 108
        out = (rct(80, 14, 40, 26, '#fffdf5', 1.4) + pth('M84,36 L95,24 L104,32 L110,26 L116,36 Z', '#94c776', .8) + circ(110, 21, 3, '#ffd84a', 0) +
               pth('M164,96 V40 M156,40 H172 L168,26 H160 Z', '#e8c48f', 1.1) +
               rct(1, 60, 54, 38, '#7f9ccf', 1.2, rx=6) + rct(-4, 72, 64, 26, '#6d89bd', 1.2, rx=6) +
               pth('M1,98 H199 V121 H1 Z', '#b98b5c', 1) + ell(100, 112, 60, 6, '#d96a5a', .8, opacity=.9))
    elif name == 'classroom':
        bg = sky or '#f2ead8'
        g = 108
        out = (rct(30, 10, 120, 50, '#2f5040', 2, stroke='#8a6a3a') + pth('M44,26 q6,-8 12,0 t12,0 M100,22 l6,10 l6,-10 M120,40 h14', 'none', 1, '#e9efe9') +
               el('text', '2 + 2 = 4', x=48, y=50, font_size=8, font_family='LB, serif', fill='#e9efe9') +
               circ(178, 22, 9, '#fff', 1.2) + pth('M178,22 V16 M178,22 H182', 'none', 1) +
               pth('M1,100 H199 V121 H1 Z', '#d4b483', 1))
    elif name == 'town':
        bg = sky or '#d7e8f2'
        g = 106
        out = ''
        for x, w, h, col in ((2, 46, 62, '#c96a50'), (48, 52, 70, '#f1e2bd'), (100, 46, 58, '#7fb8b0'), (146, 54, 66, '#d9a35f')):
            out += rct(x, 96 - h, w, h, col, 1.1)
            out += ''.join(rct(x + 6 + i * (w - 12) / 2, 96 - h + 8, (w - 18) / 2, 10, '#fdf6dc', .8) for i in range(2))
            out += pth(f'M{x + 3},{96 - h * .45:.0f} H{x + w - 3} L{x + w - 6},{96 - h * .45 + 7:.0f} H{x + 6} Z', dark(col, .8), .8)
            out += rct(x + w / 2 - 6, 80, 12, 16, '#6b4a2e', .8)
        out += pth('M1,96 H199 V121 H1 Z', '#d9d4c8', 1) + pth('M1,114 H199', 'none', .6, '#a9a396')
    elif name == 'backyard':
        bg = sky or '#d6ecf8'
        g = 106
        out = (cloud(150, 18, .8) + ''.join(pth(f'M{x},{92} V66 L{x + 5},{61} L{x + 10},66 V92 Z', '#e8c48f', .9) for x in range(-2, 200, 12)) +
               pth('M1,74 H199 M1,86 H199', 'none', 1.2, '#b38a55') +
               pth('M1,92 H199 V121 H1 Z', '#9fd27c', 1) + tufts([(20, 100, 1.4), (70, 112, 1.4), (130, 104, 1.4), (180, 114, 1.4)], '#5f9a46'))
    elif name == 'pumpkins':
        bg = sky or '#f9e3c2'
        out = (pth('M0,90 Q60,84 120,88 T200,86 V122 H0 Z', '#c8a35e', 1) +
               rct(150, 70, 36, 18, '#e7c35a', 1.1, rx=2) + pth('M152,76 H184 M152,82 H184', 'none', .7, '#b28f2e') +
               ''.join(pth(f'M{x},{88} V68 M{x - 4},74 H{x + 26}', 'none', 1.5, '#8a6a3a') for x in (10, 34)) +
               pumpkin(28, 104, .7) + pumpkin(172, 108, .8) + pumpkin(120, 92, .5) + pumpkin(64, 94, .45, '#f0a24a') +
               pth('M0,110 q30,-6 50,0 t60,2 M130,116 q30,-4 70,0', 'none', 1, '#5f7f2c'))
    elif name == 'soccer':
        bg = sky or '#d4eaf7'
        g = 106
        out = (trees_far((20, 44, 150, 174), 80) + pth('M1,80 H199 V121 H1 Z', '#8cc96d', 1) +
               ''.join(rct(x, 81, 20, 40, '#83c065', 0) for x in range(10, 200, 40)) + pth('M1,112 H199', 'none', 1.2, '#fff') +
               pth('M150,96 V62 H196 V96', 'none', 2.4, '#fff') + pth('M150,96 V62 H196 V96', 'none', .6) +
               pth(' '.join(f'M{x},62 L{x + 4},92' for x in range(154, 196, 7)) + ' ' + ' '.join(f'M150,{y} H196' for y in range(70, 96, 8)), 'none', .4, '#555'))
    elif name == 'gym':
        bg = sky or '#f1e2c6'
        g = 108
        out = (rct(1, 18, 198, 10, '#2f5aa8', 0) + rct(1, 28, 198, 3, '#d33b2f', 0) +
               rct(160, 36, 34, 24, '#fff', 1.2) + rct(171, 46, 12, 9, 'none', 1, stroke='#d33b2f') + pth('M168,60 H186', 'none', 2, '#e8823a') +
               pth('M169,60 l3,10 l3,-10 l3,10 l3,-10 l3,10 l3,-10', 'none', .6) +
               pth('M1,92 H199 V121 H1 Z', '#e2b778', 1) + pth(' '.join(f'M1,{y} H199' for y in (98, 104, 110, 116)), 'none', .4, '#c49a5a') +
               pth('M70,121 Q100,100 130,121', 'none', 1.2, '#fff'))
    elif name == 'space':
        bg = sky or '#151c40'
        g = 106
        out = (''.join(circ(x, y, .9, '#fff', 0) for x, y in ((10, 10), (30, 40), (70, 14), (95, 36), (120, 8), (150, 44), (190, 14), (176, 60), (50, 66), (8, 58))) +
               circ(160, 28, 13, '#e8823a', 1) + ell(160, 28, 22, 5, 'none', 1.4, stroke='#ffd84a') +
               pth('M0,98 Q100,88 200,98 V122 H0 Z', '#cfcfd8', 1) + ell(40, 108, 9, 2.5, '#b2b2c0', .7) + ell(150, 112, 12, 3, '#b2b2c0', .7))
    elif name == 'rain':
        bg = sky or '#bcc7d2'
        out = (curly(40, 14, 26, 9, '#e3e8ee', sw=1) + curly(150, 18, 30, 10, '#e3e8ee', sw=1) +
               pth(' '.join(f'M{x},{y} l-3,7' for x, y in ((20, 34), (50, 50), (80, 30), (110, 46), (140, 36), (170, 52), (190, 30), (34, 70), (124, 66), (182, 74))), 'none', 1, '#5a88b5') +
               pth('M0,98 Q100,92 200,98 V122 H0 Z', '#8fb27a', 1) + ell(150, 112, 18, 3.5, '#9fc7e4', .8) + ell(36, 114, 12, 2.5, '#9fc7e4', .8))
    else:                                                     # 'plain'
        bg = sky or '#efe7d4'
        g = 106
        out = pth('M1,100 H199 V121 H1 Z', dark(bg, .93), 1)
    return _frame(out, bg), g


SCENES = ['snow', 'ice', 'autumn', 'hill', 'beach', 'night', 'kitchen', 'living', 'classroom', 'town', 'backyard', 'pumpkins', 'soccer', 'gym', 'space', 'rain', 'plain']

# Painted backdrops (Jacob, 2026-10-12): scenery painted once with Grok, committed in backdrops/ with index.json.
_BD = Path(__file__).resolve().parent / 'backdrops'
PAINTED = json.loads((_BD / 'index.json').read_text()) if (_BD / 'index.json').exists() else {}
_bd_cache = {}


def painted(name):
    """(svg, ground y) for a painted backdrop: the picture fills the panel; the cast is drawn on top."""
    if name not in _bd_cache:
        b64 = base64.b64encode((_BD / f'{name}.jpg').read_bytes()).decode()
        _bd_cache[name] = el('image', href=f'data:image/jpeg;base64,{b64}', x=1, y=1, width=W - 2, height=H - 2,
                             preserveAspectRatio='xMidYMid slice')
    return _bd_cache[name], PAINTED[name].get('ground', 108)


# Painted strip (Jacob, 2026-10-12): repaint.py has Grok repaint each composed panel into painted/<key>.jpg (work dir).
PAINT_MODEL = 'grok-imagine-image-2.0'      # keeps poses, expressions and places best (tested 2026-10-12)


def painted_file(p):
    """Where repaint.py keeps this panel's painting. The key covers the composition, not the bubbles or caption."""
    import hashlib
    comp = {k: v for k, v in p.items() if k not in ('say', 'caption', 'paint')}
    h = hashlib.sha1(json.dumps([comp, PAINT_MODEL], sort_keys=True).encode()).hexdigest()[:16]
    return Path('painted') / f'{h}.jpg'


def strip_painted(spec):
    """True when every panel has its Grok painting (all or nothing, so the strip never mixes styles)."""
    panels = (spec or {}).get('panels', [])
    return (spec or {}).get('paint') is not False and len(panels) == 4 and all(painted_file(p).exists() for p in panels)


def uses_painted(spec):
    """True when a comic spec has a painted backdrop in any panel (build2.py credits Grok in the footer)."""
    return any(p.get('scene') in PAINTED for p in (spec or {}).get('panels', []))


# ---------------------------------------------------------------- free props (panel units, base at x, y)
def prop(name, x, y, s=1, opt=None):
    c = opt if isinstance(opt, str) else None
    if name == 'pumpkin':
        return pumpkin(x, y, s, c or '#e8823a')
    if name == 'tree':
        return tree(x, y, s, c or '#e0782f')
    if name == 'pine':
        return pine(x, y, s)
    if name == 'snowman':
        return (circ(x, y - 9 * s, 10 * s, '#fff', 1.2) + circ(x, y - 25 * s, 7.5 * s, '#fff', 1.2) + circ(x, y - 37 * s, 6 * s, '#fff', 1.2) +
                circ(x - 2 * s, y - 38.5 * s, .9 * s, INK, 0) + circ(x + 2 * s, y - 38.5 * s, .9 * s, INK, 0) +
                pth(f'M{x:.1f},{y - 36.5 * s:.1f} l{6 * s:.1f},{1.2 * s:.1f} l{-6 * s:.1f},{1.2 * s:.1f} Z', '#e8823a', .6) +
                circ(x, y - 27 * s, .9 * s, INK, 0) + circ(x, y - 23 * s, .9 * s, INK, 0) +
                pth(f'M{x - 7 * s:.1f},{y - 26 * s:.1f} l{-9 * s:.1f},{-6 * s:.1f} M{x + 7 * s:.1f},{y - 26 * s:.1f} l{9 * s:.1f},{-7 * s:.1f}', 'none', 1.1, '#7a5a35'))
    if name == 'leafpile':
        col = c or '#e0782f'
        return (pth(f'M{x - 24 * s:.1f},{y:.1f} Q{x - 20 * s:.1f},{y - 20 * s:.1f} {x:.1f},{y - 22 * s:.1f} Q{x + 20 * s:.1f},{y - 20 * s:.1f} {x + 24 * s:.1f},{y:.1f} Z', col, 1.1) +
                ''.join(leaf(x + dx * s, y + dy * s, 3 * s, cc) for dx, dy, cc in ((-12, -10, '#d9a520'), (4, -16, '#c9443b'), (14, -7, '#d9a520'), (-2, -6, '#c9443b'))))
    if name == 'boot':
        return grp(pth('M0,0 L0,-16 L14,-16 L14,-6 L26,-2 L26,4 L0,4 Z', '#8a5a2b', 1.2) + rct(0, -19, 14, 4, '#5e3b18', 1), f'translate({x - 13 * s:.1f},{y - 4 * s:.1f}) scale({s})')
    if name == 'ball':
        return soccer(x, y - 8 * s, 8 * s)
    if name == 'basketball':
        return bball(x, y - 8 * s, 8 * s)
    if name == 'kite':
        col = c or '#e0457b'
        return (pth(f'M{x:.1f},{y - 14 * s:.1f} L{x + 10 * s:.1f},{y:.1f} L{x:.1f},{y + 16 * s:.1f} L{x - 10 * s:.1f},{y:.1f} Z', col, 1.1) +
                pth(f'M{x:.1f},{y - 14 * s:.1f} V{y + 16 * s:.1f} M{x - 10 * s:.1f},{y:.1f} H{x + 10 * s:.1f}', 'none', .7) +
                pth(f'M{x:.1f},{y + 16 * s:.1f} q-6,8 0,14 t-2,14', 'none', .7) +
                ''.join(pth(f'M{x + dx:.1f},{y + 16 * s + dy:.1f} l-3,2 l3,2 Z', '#ffd84a', .6) for dx, dy in ((-3, 8), (-2, 20))))
    if name == 'hole':
        return ell(x, y, 20 * s, 6 * s, '#3f6f98', 1.2) + pth(f'M{x - 12 * s:.1f},{y - 1:.1f} q6,-2 12,0', 'none', .7, '#8fb6d2')
    if name == 'bucket':
        col = c or '#e0457b'
        return pth(f'M{x - 8 * s:.1f},{y - 16 * s:.1f} L{x + 8 * s:.1f},{y - 16 * s:.1f} L{x + 6 * s:.1f},{y:.1f} L{x - 6 * s:.1f},{y:.1f} Z', col, 1.1) + \
            pth(f'M{x - 8 * s:.1f},{y - 16 * s:.1f} Q{x:.1f},{y - 28 * s:.1f} {x + 8 * s:.1f},{y - 16 * s:.1f}', 'none', .9)
    if name == 'sandcastle':
        return grp(rct(-16, -14, 32, 14, '#e8c77f', 1) + rct(-20, -24, 12, 24, '#e8c77f', 1) + rct(8, -24, 12, 24, '#e8c77f', 1) +
                   pth('M-20,-24 v-3 h3 v3 h3 v-3 h3 v3 M8,-24 v-3 h3 v3 h3 v-3 h3 v3', 'none', .9) + pth('M14,-27 V-36 L20,-33 L14,-31', '#e0457b', .8) +
                   pth('M-4,0 V-7 Q0,-11 4,-7 V0', '#6b4a2e', .8), f'translate({x:.1f},{y:.1f}) scale({s})')
    if name == 'gift':
        return gift(x, y, s, c)
    if name == 'cake':
        return grp(rct(-14, -14, 28, 14, '#f6c3d6', 1.1) + rct(-11, -24, 22, 10, '#fff4e0', 1.1) + pth('M-14,-12 q3.5,4 7,0 t7,0 t7,0 t7,0', 'none', 1, '#e0457b') +
                   ''.join(rct(dx - .8, -31, 1.6, 7, '#8fd3e6', .5) + pth(f'M{dx},-31 q-1.6,-2.5 0,-4.5 q1.6,2 0,4.5 Z', '#ffb43a', 0) for dx in (-6, 0, 6)),
                   f'translate({x:.1f},{y:.1f}) scale({s})')
    if name == 'table':
        return grp(rct(-24, -24, 48, 4, '#b98b5c', 1.1) + rct(-21, -20, 3, 20, '#9a7044', 1) + rct(18, -20, 3, 20, '#9a7044', 1), f'translate({x:.1f},{y:.1f}) scale({s})')
    if name == 'campfire':
        return grp(pth('M-12,0 L12,-5 M-12,-5 L12,0', 'none', 3.4, '#7a5a35') + pth('M-8,-3 Q-10,-14 -2,-22 Q-3,-14 2,-12 Q2,-20 6,-24 Q12,-12 8,-3 Z', '#f6a33a', 1) +
                   pth('M-3,-4 Q-4,-11 0,-15 Q2,-10 4,-9 Q5,-6 3,-4 Z', '#ffe08a', 0), f'translate({x:.1f},{y:.1f}) scale({s})')
    if name == 'tent':
        col = c or '#2f7d4f'
        return grp(pth('M-26,0 L0,-34 L26,0 Z', col, 1.2) + pth('M0,-34 L-6,0 H6 Z', dark(col, .6), 1), f'translate({x:.1f},{y:.1f}) scale({s})')
    if name == 'puddle':
        return ell(x, y - 2, 18 * s, 3.5 * s, '#9fc7e4', .8)
    if name == 'rock':
        return pth(f'M{x - 12 * s:.1f},{y:.1f} Q{x - 10 * s:.1f},{y - 12 * s:.1f} {x:.1f},{y - 12 * s:.1f} Q{x + 12 * s:.1f},{y - 10 * s:.1f} {x + 13 * s:.1f},{y:.1f} Z', '#a8a39a', 1.1)
    if name == 'flowers':
        return ''.join(pth(f'M{x + dx * s:.1f},{y:.1f} V{y - 10 * s:.1f}', 'none', 1, '#3f8a3a') + circ(x + dx * s, y - 12 * s, 3 * s, cc, .8) + circ(x + dx * s, y - 12 * s, 1.1 * s, '#ffd84a', 0)
                       for dx, cc in ((-8, '#f6a6c6'), (0, '#c4a3ef'), (8, '#e0457b')))
    if name == 'bench':
        return grp(rct(-26, -14, 52, 4, '#a87b45', 1) + rct(-26, -24, 52, 4, '#a87b45', 1) + rct(-22, -10, 3, 10, '#555', .8) + rct(19, -10, 3, 10, '#555', .8),
                   f'translate({x:.1f},{y:.1f}) scale({s})')
    if name == 'sled':
        col = c or '#c9443b'
        return grp(rct(-20, -9, 40, 5, col, 1.1, rx=2) + pth('M-22,-2 H20 Q26,-2 26,-8', 'none', 1.4) + pth('M-14,-4 V-2 M12,-4 V-2', 'none', 1.2), f'translate({x:.1f},{y:.1f}) scale({s})')
    if name == 'bush':
        return curly(x, y - 9 * s, 16 * s, 10 * s, c or '#7fbf6a', sw=1)
    if name == 'snowpile':
        return curly(x, y - 6 * s, 20 * s, 8 * s, '#ffffff', sw=1, stroke='#8aa6bb')
    if name == 'fish':
        return fish(x, y - 23 * s, s, c)
    if name == 'trophy':
        return trophy(x, y, s)
    if name == 'stars':
        return sparkle(x, y, 4 * s) + sparkle(x + 8 * s, y - 6 * s, 3 * s) + sparkle(x - 7 * s, y - 8 * s, 2.5 * s)
    if name == 'hearts':
        return ''.join(pth(f'M{x + dx:.1f},{y + dy + 3 * s:.1f} c{-5 * s:.1f},{-3 * s:.1f} {-3 * s:.1f},{-8 * s:.1f} 0,{-5 * s:.1f} c{3 * s:.1f},{-3 * s:.1f} {5 * s:.1f},{2 * s:.1f} 0,{5 * s:.1f} Z', '#e0457b', .7)
                       for dx, dy in ((0, 0), (9 * s, -7 * s), (-7 * s, -10 * s)))
    if name == 'cloud':
        return cloud(x, y, s)
    if name == 'sun':
        return circ(x, y, 10 * s, '#ffd84a', 1) + pth(' '.join(f'M{x + 13 * s * math.cos(t):.1f},{y + 13 * s * math.sin(t):.1f} L{x + 17 * s * math.cos(t):.1f},{y + 17 * s * math.sin(t):.1f}' for t in [i * math.pi / 4 for i in range(8)]), 'none', 1.2, '#e8a92a')
    if name == 'sfx':
        txt = esc(opt or 'POP!')
        return (el('text', txt, x=x, y=y, font_size=13 * s, font_family='PF, serif', font_weight=700, text_anchor='middle',
                   fill='#ffd84a', stroke=INK, stroke_width=2.6 * s, stroke_linejoin='round', paint_order='stroke', transform=f'rotate(-8 {x} {y})'))
    if name in HELD:
        return held(name, x, y, s)
    raise SystemExit(f"comic: unknown prop '{name}' (props: {', '.join(PROPS)})")


PROPS = ['pumpkin', 'tree', 'pine', 'snowman', 'leafpile', 'boot', 'ball', 'basketball', 'kite', 'hole', 'bucket', 'sandcastle', 'gift', 'cake',
         'table', 'campfire', 'tent', 'puddle', 'rock', 'flowers', 'bench', 'sled', 'bush', 'snowpile', 'fish', 'trophy', 'stars', 'hearts',
         'cloud', 'sun', 'sfx'] + [h for h in HELD if h not in ('pumpkin', 'ball', 'basketball', 'gift', 'fish', 'trophy')]


# ---------------------------------------------------------------- bubbles
CHAR_W = 4.75                                  # Libre Baskerville at 8.2 px: a safe average glyph width


def wrap(text, width=20):
    if isinstance(text, list):
        return [str(t) for t in text]
    words, lines, cur = str(text).split(), [], ''
    for w_ in words:
        if cur and len(cur) + 1 + len(w_) > width:
            lines.append(cur)
            cur = w_
        else:
            cur = (cur + ' ' + w_).strip()
    return lines + ([cur] if cur else [])


def bubble_svg(kind, x, y, w, lines, tail):
    h = 10 * len(lines) + 7
    t = ''.join(el('text', esc(l), x=x + w / 2, y=y + 12.5 + i * 10, text_anchor='middle', font_size=8.2, font_family='LB, serif', fill=INK)
                for i, l in enumerate(lines))
    tx, ty = tail
    bx = max(x + 7, min(x + w - 7, tx))
    if kind == 'think':
        body = curly(x + w / 2, y + h / 2, w / 2, h / 2 + 1, '#fff', n=max(10, int(w / 9)), sw=1.2)
        dots = ''.join(circ(bx + (tx - bx) * f, y + h + 2 + (ty - y - h - 2) * f, r, '#fff', 1) for f, r in ((.25, 2.6), (.6, 1.8), (.9, 1.2))) if ty > y + h + 4 else ''
        return grp(body + dots + t)
    if kind == 'shout':
        n_ = max(12, int((w + h) / 5))
        pts = []
        for i in range(n_ * 2):
            a = 2 * math.pi * i / (n_ * 2)
            k = 1.0 if i % 2 == 0 else 1.18
            pts.append(f'{x + w / 2 + (w / 2 + 2) * k * math.cos(a):.1f},{y + h / 2 + (h / 2 + 2) * k * math.sin(a):.1f}')
        spike = ''
        if ty > y + h + 4:
            spike = pth(f'M{bx - 5:.1f},{y + h:.1f} L{bx + 5:.1f},{y + h:.1f} L{tx:.1f},{ty:.1f} Z', '#fff7c2', 1.2)
        return grp(spike + pth('M' + ' L'.join(pts) + ' Z', '#fff7c2', 1.2) + t.replace('font-family="LB, serif"', 'font-family="LB, serif" font-weight="700"'))
    tail_svg = ''
    if ty > y + h + 2:
        tail_svg = (pth(f'M{bx - 4:.1f},{y + h - 1:.1f} L{bx + 4:.1f},{y + h - 1:.1f} L{tx:.1f},{ty:.1f} Z', '#fff', 1.2) +
                    rct(bx - 3.6, y + h - 2.6, 7.2, 3.6, '#fff', 0))
    return grp(rct(x, y, w, h, '#fff', 1.2, rx=7) + tail_svg + t)


def caption(text, x=4, y=4):
    lines = wrap(text, 26)
    w = max(len(l) for l in lines) * 4.3 + 10
    h = 9 * len(lines) + 5
    return grp(rct(x, y, w, h, '#fff1b8', 1) + ''.join(el('text', esc(l), x=x + 5, y=y + 10 + i * 9, font_size=7.4, font_family='LB, serif',
                                                          font_style='italic', fill=INK) for i, l in enumerate(lines))), (x, y, w, h)


# ---------------------------------------------------------------- panel and strip
def panel(p, idx=0, warn=None):
    warn = warn if warn is not None else []
    name = p.get('scene', 'plain')
    art_img = ''
    if p.get('paint'):                         # comic() sets this when the whole strip is painted
        b64 = base64.b64encode(painted_file(p).read_bytes()).decode()
        art_img = el('image', href=f'data:image/jpeg;base64,{b64}', x=1, y=1, width=W - 2, height=H - 2, preserveAspectRatio='xMidYMid slice')
    if name in PAINTED:
        bg, ground = painted(name)
        if p.get('sky'):
            warn.append(f"panel {idx + 1}: 'sky' does nothing on the painted backdrop '{name}' (use mirror or another backdrop)")
    else:
        if name not in SCENES:
            warn.append(f"panel {idx + 1}: unknown scene '{name}', drawn as 'plain' (python art.py --list)")
        bg, ground = scene(name, p.get('sky'))
    if p.get('mirror'):
        bg = grp(bg, f'translate({W},0) scale(-1,1)')
    back_props, front_props, cast_svg, heads = '', '', '', {}
    shadows = ''                                  # painted scenes only: a soft shadow sets each character on the ground
    for pr in p.get('props', []):
        if isinstance(pr, dict):
            name, x, y, s, opt, front = pr['name'], pr.get('x', 100), pr.get('y', ground), pr.get('s', 1), pr.get('opt'), pr.get('front')
        else:
            name, x, y, s, opt, front = (list(pr) + [None] * 6)[:6]
            y = ground if y is None else y
            s = s or 1
        svg = prop(name, x, y, s, opt)
        if front:
            front_props += svg
        else:
            back_props += svg
    for c in p.get('cast', []):
        C = who(c['who'])
        x = c.get('x', 100)
        y = c.get('y', ground)
        s = C.scale * c.get('s', 1)
        flip = c.get('flip', x > 100)
        fig = figure(C, c.get('pose', 'stand'), c.get('face', 'happy'), c.get('gear'), c.get('hold'), c.get('hold_opt'), c.get('shirt'), flip)
        cast_svg += grp(fig, f'translate({x:.1f},{y:.1f}) scale({-s if flip else s:.3f},{s:.3f})')
        if name in PAINTED:
            shadows += ell(x, y + .5, 24 * s, 2.6, INK, 0, opacity=.2)
        hx, hy, hr = C.head
        lift = (C.sit_drop if c.get('pose') == 'sit' else POSES.get(c.get('pose', 'stand'), {}).get('dy', 0))
        wx = x + (-1 if flip else 1) * s * hx
        heads[C.key] = (wx, y + s * (hy + lift), s * hr, y + s * (C.top + lift))
    out, rects = '', []
    for cap in p.get('caption', []) if isinstance(p.get('caption'), list) else ([p['caption']] if p.get('caption') else []):
        svg, r = caption(cap)
        out += svg
        rects.append(r)
    for b in p.get('say', []):
        lines = wrap(b.get('text', ''), b.get('wrap', 20))
        w = b.get('w') or max(len(l) for l in lines) * CHAR_W + 12
        h = 10 * len(lines) + 7
        pad = 6 if b.get('kind') == 'shout' else 0
        spk = heads.get(who(b['who']).key) if b.get('who') else None
        if b.get('who') and not spk:
            warn.append(f"panel {idx + 1}: '{b['who']}' speaks but is not in the cast")
        sx = spk[0] if spk else 100
        x = b.get('x', max(3 + pad, min(W - 3 - pad - w, sx - w / 2)))
        y = b.get('y', 3 + pad)
        if 'x' not in b and 'y' not in b:
            for (rx, ry, rw, rh) in rects:
                if x - pad < rx + rw + 2 and rx < x + w + pad + 2 and y - pad < ry + rh + 2 and ry < y + h + pad + 2:
                    right = max(3 + pad, min(W - 3 - pad - w, rx + rw + 3 + pad))
                    left = max(3 + pad, min(W - 3 - pad - w, rx - w - 3 - pad))
                    for nx in sorted((right, left), key=lambda v: abs(v - (sx - w / 2))):
                        if not (nx - pad < rx + rw + 2 and rx < nx + w + pad + 2):
                            x = nx
                            break
                    else:
                        y = ry + rh + 3 + pad
        tail = (sx, spk[3] - 2) if spk else (x + w / 2, y + h)
        if w > W - 6:
            warn.append(f"panel {idx + 1}: bubble '{lines[0]}...' is wider than the panel")
        for k, (hx, hy, hr, top) in heads.items():
            if x < hx + hr * .9 and hx - hr * .9 < x + w and y < hy + hr * .6 and hy - hr * .5 < y + h:
                warn.append(f"panel {idx + 1}: bubble '{lines[0]}' covers {CAST[k].name}'s face")
        rects.append((x, y, w, h))
        out += bubble_svg(b.get('kind', 'say'), x, y, w, lines, tail)
    frame = rct(1, 1, W - 2, H - 2, 'none', 2)
    pic = art_img or f'{bg}{shadows}{back_props}{cast_svg}{front_props}'     # Grok's painting replaces the drawn art
    return f'<svg viewBox="0 0 {W} {H}" width="100%" xmlns="http://www.w3.org/2000/svg">{pic}{out}{frame}</svg>'


SAMPLE = {
    "title": "ARTIC & BIG BEAR",
    "panels": [
        {"scene": "pumpkins", "cast": [
            {"who": "bear", "x": 50, "pose": "hold", "face": "happy", "gear": {"scarf": "#2f7d4f"}, "hold": "pumpkin"},
            {"who": "fox", "x": 150, "pose": "point", "face": "surprised"}],
         "say": [{"who": "fox", "text": "That pumpkin is so tiny!"}]},
        {"scene": "pumpkins", "sky": "#f6d9b0", "cast": [
            {"who": "bear", "x": 48, "pose": "akimbo", "face": "proud", "gear": {"scarf": "#2f7d4f"}},
            {"who": "mack", "x": 150, "pose": "sit", "face": "grin"}],
         "say": [{"who": "bear", "text": "Small, but it's all mine."}]},
        {"scene": "pumpkins", "cast": [
            {"who": "uni", "x": 60, "pose": "wave", "face": "grin"},
            {"who": "bob", "x": 148, "pose": "tada", "face": "wink", "gear": {"cap": "#d33b2f"}}],
         "props": [["pumpkin", 104, 106, 2.4]],
         "say": [{"who": "bob", "text": "Ours is HUGE!"}]},
        {"scene": "pumpkins", "sky": "#f3cf9f", "cast": [
            {"who": "bear", "x": 48, "pose": "facepalm", "face": "sad", "gear": {"scarf": "#2f7d4f"}},
            {"who": "fox", "x": 150, "pose": "shrug", "face": "laugh"}],
         "props": [["pumpkin", 100, 106, 0.6]],
         "say": [{"who": "fox", "text": "Size isn't everything!"}]},
    ],
}


def comic(spec=None, warn=None):
    """The strip at the bottom of the page. spec = edition.json `comic` (README: Comic)."""
    spec = spec or SAMPLE
    warns = [] if warn is None else warn
    panels = spec.get('panels', [])
    if len(panels) != 4:
        raise SystemExit(f'comic: needs exactly 4 panels, got {len(panels)}')
    paint = strip_painted(spec)
    if not paint and spec.get('paint') is not False and any(painted_file(p).exists() for p in panels):
        warns.append('only some panels are painted (a panel changed since repaint.py ran?): printing the drawn strip; run repaint.py again')
    svgs = ''.join(panel({**p, 'paint': paint}, i, warns) for i, p in enumerate(panels))
    if warn is None:
        for w_ in warns:
            print('COMIC WARNING:', w_, file=sys.stderr)
    title = esc(spec.get('title', 'ARTIC &amp; BIG BEAR'))
    return f'<div class="comic"><div class="ct">{title}</div><div class="cg">{svgs}</div></div>'


# ---------------------------------------------------------------- weather icons (Jacob, 2026-10-12)
# Original drawn icons for the weather box, picked from the NWS wording ("Sunny", "Rain Likely", ...).
WX_ICONS = ['sun', 'mostly_sunny', 'partly', 'cloudy', 'showers', 'rain', 'storm', 'snow', 'fog', 'wind', 'moon']
WX_SUN, WX_CLOUD, WX_GREY, WX_RAIN = '#f5b82e', '#ffffff', '#b9bec6', '#3b7fc4'


def wx_kind(text):
    """The icon for a forecast phrase, or None. Only the first sentence counts ('Sunny. ... Rain likely Sunday.')."""
    t = re.sub(r'<[^>]+>', ' ', text or '').lower()
    t = re.split(r'[.;]', t.strip(), maxsplit=1)[0]
    has = lambda *w: any(x in t for x in w)
    if has('thunder', 't-storm', 'tstorm'): return 'storm'
    if has('snow', 'flurr', 'sleet', 'wintry', 'ice pellet', 'freezing'): return 'snow'
    if has('rain', 'shower', 'drizzle', 'sprinkle'):
        return 'showers' if has('chance', 'slight', 'scattered', 'isolated', 'partly', 'sunny', 'then') else 'rain'
    if has('fog', 'haze', 'mist', 'smoke'): return 'fog'
    if has('overcast') or ('cloudy' in t and 'partly cloudy' not in t): return 'cloudy'
    if has('partly', 'mostly sunny', 'mostly clear', 'increasing clouds', 'decreasing clouds', 'clouds'):
        return 'mostly_sunny' if has('mostly sunny', 'mostly clear') else 'partly'
    if has('sunny', 'clear', 'fair', 'hot'): return 'sun'
    if has('wind', 'breezy', 'blustery', 'gust'): return 'wind'
    return None


def _wx_sun(cx, cy, r):
    rays = ''.join(pth(f'M{cx + (r + 2.2) * math.cos(a):.1f},{cy + (r + 2.2) * math.sin(a):.1f} '
                       f'L{cx + (r + 5.4) * math.cos(a):.1f},{cy + (r + 5.4) * math.sin(a):.1f}', 'none', 1.5, '#e09a12')
                   for a in (i * math.pi / 4 for i in range(8)))
    return rays + circ(cx, cy, r, WX_SUN, 1.3) + crescent(cx, cy, r, r, '#e09a12', op=.35)


def _wx_cloud(x, y, s=1, fill=WX_CLOUD):
    """A puffy cloud whose flat bottom sits at y, centered on x."""
    bumps = [(-8, -4, 5.5), (-1.5, -8.5, 7.5), (7, -5, 6), (11, -1.5, 3.8), (-12, -1, 3.6)]
    outline = ''.join(circ(x + dx * s, y + dy * s, r * s, fill, 1.3) for dx, dy, r in bumps)
    body = ''.join(circ(x + dx * s, y + dy * s, r * s - .65, fill, 0) for dx, dy, r in bumps)
    base = pth(f'M{x - 12 * s:.1f},{y + 2.6 * s:.1f} H{x + 11 * s:.1f}', 'none', 1.3)
    return outline + rct(x - 12 * s, y - 3 * s, 23 * s, 5.6 * s, fill, 0) + body + base


def _wx_drops(x, y, n=3, col=WX_RAIN):
    return ''.join(pth(f'M{x + i * 6:.1f},{y:.1f} l-2,5', 'none', 1.8, col) for i in range(n))


def weather_icon(kind, px=30):
    """An inline SVG icon (40x40 viewBox) for wx_kind(); '' for None or an unknown kind."""
    if kind not in WX_ICONS:
        return ''
    g = {
        'sun': lambda: _wx_sun(20, 20, 9),
        'mostly_sunny': lambda: _wx_sun(17, 17, 9) + _wx_cloud(27, 33, .62),
        'partly': lambda: _wx_sun(14, 14, 8) + _wx_cloud(23, 32, .95),
        'cloudy': lambda: _wx_cloud(15, 22, .7, '#e4e7eb') + _wx_cloud(21, 31, 1.05),
        'showers': lambda: _wx_sun(13, 12, 7) + _wx_cloud(22, 26, .95) + _wx_drops(16, 31),
        'rain': lambda: _wx_cloud(20, 24, 1.1, '#dfe3e8') + _wx_drops(13, 29, 4),
        'storm': lambda: _wx_cloud(20, 23, 1.1, WX_GREY) + _wx_drops(10, 28, 2) +
                         pth('M22,24 L17,32 H21 L18,39 L26,29 H22 L25,24 Z', WX_SUN, 1.1),
        'snow': lambda: _wx_cloud(20, 23, 1.1, '#e8edf3') + ''.join(
            pth(f'M{x},{y - 3} V{y + 3} M{x - 2.6},{y - 1.5} L{x + 2.6},{y + 1.5} M{x - 2.6},{y + 1.5} L{x + 2.6},{y - 1.5}',
                'none', 1.1, WX_RAIN) for x, y in ((12, 32), (20, 35), (28, 32))),
        'fog': lambda: _wx_cloud(20, 18, .9, '#e4e7eb') + ''.join(
            pth(f'M{x0},{y} q3,-2 6,0 t6,0 t6,0 t6,0', 'none', 1.5, '#8a9099') for x0, y in ((7, 25), (10, 30), (7, 35))),
        'wind': lambda: ''.join(pth(d, 'none', 1.8, '#5a7d9a') for d in
                                ('M5,14 H24 a4,4 0 1 0 -4,-4', 'M5,21 H31 a4.5,4.5 0 1 1 -4.5,4.5', 'M8,28 H20 a3.5,3.5 0 1 1 -3.5,3.5')),
        'moon': lambda: pth('M25,8 A12,12 0 1 0 32,26 A9.5,9.5 0 1 1 25,8 Z', '#f3dc8a', 1.3),
    }[kind]()
    return (f'<svg class="wxi" viewBox="0 0 40 40" width="{px}" height="{px}" xmlns="http://www.w3.org/2000/svg" '
            f'role="img" aria-label="{kind.replace("_", " ")}">{g}</svg>')


# ---------------------------------------------------------------- library listing and model sheet
def library():
    return {'cast': {k: c.name for k, c in CAST.items()}, 'poses': list(POSES), 'faces': list(FACES), 'gear': GEAR,
            'held': HELD, 'props': PROPS, 'scenes': SCENES,
            'painted scenes': {k: f"{v['season']}: {v['subject']}" for k, v in PAINTED.items()}, 'weather icons': WX_ICONS}


def sheet():
    cell = lambda inner, label: (f'<div class="cell"><svg viewBox="0 0 120 100" xmlns="http://www.w3.org/2000/svg">'
                                 f'{rct(0, 0, 120, 100, "#f6f1e3", 0)}{pth("M0,92 H120", "none", .6, "#bbb")}{inner}</svg><div>{label}</div></div>')
    rows = []
    for C in CAST.values():
        figs = ''.join(cell(grp(figure(C, p), f'translate(60,92) scale({C.scale * 1.05:.2f})'), p) for p in POSES)
        faces = ''.join(cell(grp(figure(C, 'stand', f), f'translate(60,{92 + C.top * C.scale * 1.7 * -.42:.0f}) scale({C.scale * 1.7:.2f})'), f) for f in FACES)
        rows.append(f'<h2>{C.name} <small>({C.key})</small></h2><div class="row">{figs}</div><div class="row">{faces}</div>')
    gear_demo = ''.join(cell(grp(figure(CAST[k], 'stand', 'happy', {g_: True}), f'translate(60,92) scale({CAST[k].scale * 1.05:.2f})'), g_)
                        for g_, k in zip(GEAR, ['bear', 'fox', 'uni', 'bob', 'mack', 'bear', 'uni', 'fox', 'bob', 'bear', 'bob', 'mack']))
    held_demo = ''.join(cell(grp(figure(CAST[k], 'hold', 'happy', hold=h), f'translate(60,92) scale({CAST[k].scale * 1.05:.2f})'), h)
                        for h, k in zip(HELD, list(CAST) * 5))
    props_demo = ''.join(cell(prop(p, 60, 92, 1, None) if p not in ('kite', 'cloud', 'sun', 'stars', 'hearts', 'sfx') else prop(p, 60, 50, 1, None), p) for p in PROPS)
    scenes = ''.join(f'<div class="cell wide"><svg viewBox="0 0 200 122" xmlns="http://www.w3.org/2000/svg">{scene(s)[0]}{rct(1, 1, 198, 120, "none", 2)}</svg><div>{s}</div></div>' for s in SCENES)
    gl = lambda k: pth(f'M1,{PAINTED[k].get("ground", 108)} H199', 'none', .7, '#d33b2f', stroke_dasharray='3 2')   # where feet go
    painted_demo = ''.join(f'<div class="cell wide"><svg viewBox="0 0 200 122" xmlns="http://www.w3.org/2000/svg">{painted(k)[0]}{gl(k)}{rct(1, 1, 198, 120, "none", 2)}</svg>'
                           f'<div>{k} <small>({v["season"]})</small></div></div>' for k, v in PAINTED.items())
    return f'''<!doctype html><html><head><meta charset="utf-8"><title>Comic cast sheet</title><style>
body{{font-family:Georgia,serif;margin:16px;background:#fff;color:{INK}}} h2{{margin:14px 0 4px;font-size:16px}} small{{color:#777;font-weight:400}}
.row{{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:4px}} .cell{{width:120px;text-align:center;font-size:11px}} .cell svg{{width:120px;height:100px;display:block}}
.wide{{width:200px}} .wide svg{{width:200px;height:122px}}</style></head><body><h1>Fairfax Daily Scoop: comic cast</h1>
{"".join(rows)}<h2>Gear</h2><div class="row">{gear_demo}</div><h2>Held props</h2><div class="row">{held_demo}</div>
<h2>Props</h2><div class="row">{props_demo}</div>
<h2>Weather icons</h2><div class="row">{''.join(f'<div class="cell">{weather_icon(k, 80)}<div>{k}</div></div>' for k in WX_ICONS)}</div><h2>Scenes</h2><div class="row">{scenes}</div>
<h2>Painted scenes <small>(Grok backdrops; dashed line = ground)</small></h2><div class="row">{painted_demo}</div>
<h2>Sample strip</h2><div style="width:7.6in">{comic(SAMPLE).replace('class="cg"', 'style="display:grid;grid-template-columns:repeat(4,1fr);gap:3px"')}</div></body></html>'''


if __name__ == '__main__':
    if '--list' in sys.argv:
        for k, v in library().items():
            print(f'{k}: {", ".join(f"{a} ({b})" for a, b in v.items()) if isinstance(v, dict) else ", ".join(v)}')
    elif '--sheet' in sys.argv:
        out = sys.argv[sys.argv.index('--sheet') + 1] if len(sys.argv) > sys.argv.index('--sheet') + 1 else 'cast.html'
        open(out, 'w').write(sheet())
        print('wrote', out)
    else:
        print(__doc__)
