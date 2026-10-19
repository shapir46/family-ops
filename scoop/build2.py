import base64, glob, json, re, sys
import art
import crossword
import sudoku
import os
G=os.environ.get("FONTDIR","./fonts")
def f(p): return base64.b64encode(open(glob.glob(p)[0],'rb').read()).decode()
frak=f(f"{G}/fontsource-grenze-gotisch*/package/files/grenze-gotisch-latin-700-normal.woff2")
pf4=f(f"{G}/fontsource-playfair-display*/package/files/playfair-display-latin-400-normal.woff2")
pf7=f(f"{G}/fontsource-playfair-display*/package/files/playfair-display-latin-700-normal.woff2")
lb4=f(f"{G}/fontsource-libre-baskerville*/package/files/libre-baskerville-latin-400-normal.woff2")
lb7=f(f"{G}/fontsource-libre-baskerville*/package/files/libre-baskerville-latin-700-normal.woff2")
d=json.load(open('edition.json'))
_MONTHS = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
def edition_days():
    """ISO dates this edition covers, from `date` ("Thursday, October 15, 2026" or "Saturday & Sunday, October 17–18, 2026")."""
    m = re.search(r'([A-Za-z]+) (\d{1,2})(?:\s*[–-]\s*(\d{1,2}))?, (\d{4})', d.get('date', ''))
    if not m or m.group(1).lower() not in _MONTHS: return []
    mo, a, b, y = _MONTHS.index(m.group(1).lower()) + 1, int(m.group(2)), int(m.group(3) or m.group(2)), int(m.group(4))
    return [f"{y}-{mo:02d}-{day:02d}" for day in range(a, b + 1)]
_KIT = os.path.dirname(os.path.abspath(__file__))
# Assigned stories: a one-time headline story Jacob asks for, written ahead with his own photo, in assigned/queue.json.
# The entry whose date falls in this edition replaces the headline story (README: Assigned stories, Jacob 2026-10-15).
if os.path.exists(os.path.join(_KIT, 'assigned', 'queue.json')):
    _due = [e for e in json.load(open(os.path.join(_KIT, 'assigned', 'queue.json'))) if e.get('date') in edition_days()]
    if _due:
        a = _due[0]
        d.update(head=a['head'], sub=a['sub'], story=a['story'], head_src=a['head_src'])
        if a.get('photo'): d['head_photo'] = dict(a['photo'], img=os.path.join(_KIT, a['photo']['img']))
        else: d.pop('head_photo', None)
        print(f"ASSIGNED STORY: {a['head']}", file=sys.stderr)
crit_b64=''
if d.get('critter') and d['critter'].get('img'):
    from PIL import Image; import io
    im=Image.open(d['critter']['img']).convert('RGB'); im.thumbnail((500,400)); bio=io.BytesIO(); im.save(bio,'JPEG',quality=82); crit_b64=base64.b64encode(bio.getvalue()).decode()
hp_b64=''
if d.get('head_photo') and d['head_photo'].get('img'):
    from PIL import Image; import io
    im=Image.open(d['head_photo']['img']).convert('RGB'); im.thumbnail((900,500)); bio=io.BytesIO(); im.save(bio,'JPEG',quality=85); hp_b64=base64.b64encode(bio.getvalue()).decode()
head_icon_html=''
head_photo_html=(f"<div style='border:1px solid #161410;line-height:0'><img src='data:image/jpeg;base64,{hp_b64}' style='width:100%;height:auto;max-height:{int(d["head_photo"].get("h", 190))}px;object-fit:cover'></div>") if hp_b64 else ''
# No real photo: an original topic icon in a badge, so the lead always has a visual (Jacob, 2026-10-19). The badge
# floats at the top right of the story's first column and the text wraps around it, leaving no empty band.
# edition.json `head_icon` names one (art.py HEAD_ICONS); otherwise art.py picks it from the headline's words.
if not hp_b64 and d.get('head'):
    _hi = d.get('head_icon') or art.head_icon_for(d['head'], d.get('sub', ''), ' '.join(d.get('story') or []))
    if _hi not in art.HEAD_ICONS:
        print(f"HEAD ICON WARNING: unknown head_icon '{_hi}' (known: {', '.join(art.HEAD_ICONS)}); using star", file=sys.stderr)
    print(f"HEAD ICON: {_hi}", file=sys.stderr)
    head_icon_html = f"<span class='hi-float'><span class='hi-badge'>{art.head_icon(_hi, 48)}</span></span>"
li=lambda xs:"".join(f"<li>{x}</li>" for x in xs)
# Soft hyphens in long words of the stories, so justified lines (narrow ones beside the headline icon especially)
# break inside words instead of opening wide gaps; Chromium here has no hyphenation dictionary (Jacob, 2026-10-19).
try:
    import pyphen
    _hyph = pyphen.Pyphen(lang='en_US', left=3, right=3)
except ImportError:
    _hyph = None
    print("HYPHENATION WARNING: pyphen is not installed (run scripts/bootstrap.sh); stories print without soft hyphens", file=sys.stderr)
def hyph(h):
    if not _hyph: return h
    return re.sub(r'(<[^>]*>)|([A-Za-z]{7,})', lambda m: m.group(1) or _hyph.inserted(m.group(2), hyphen='\u00ad'), h)
def story(h,t,*_): return f"<h3>{h}</h3><p>{hyph(t)}</p>"   # no source line on the page; sources go in the footer (Jacob, 2026-10-12)

# ---- Sections: each returns HTML ('' = omit). The layout below places them. ----
def sec_schedule():
    return (f"<h2>{d.get('sched_title', 'The Family Schedule')}</h2><ul class='sched small'>{li(d.get('sched', []))}</ul>"
            ) if d.get('sched') else ''
def sec_week():
    return (f"<div class='box2'><h2 style='border:0;margin:0'>{d.get('week_title', 'Coming Up')}</h2><ul class='small'>{li(d['week'])}</ul></div>") if d.get('week') else ''
def sec_school_notes():
    return (f"<h2>{d.get('notes_title', 'Quarton Notes')}</h2><ul class='small'>{li(d['quarton'])}</ul>") if d.get('quarton') else ''
def sec_left_story():
    if d.get('critter'):
        c = d['critter']
        return (f"<h2>Cutest Critter</h2><div style='border:1px solid #161410;line-height:0'><img src='data:image/jpeg;base64,{crit_b64}' style='width:100%;height:auto;max-height:150px;object-fit:cover'></div>"
                f"<div class='cap' style='text-align:center'><b>{c['name']}</b> — {c['fact']}</div>")
    return story(*d['news'][2]) if len(d.get('news', [])) > 2 else ''
def sec_lead():
    paras = [f'<p>{hyph(x)}</p>' for x in d['story']]
    if head_icon_html and paras: paras[0] = '<p>' + head_icon_html + paras[0][3:]
    return (f"<div class='headline'>{d['head']}</div><div class='sub'>{d['sub']}</div>{head_photo_html}"
            f"<div class='cols2'>{''.join(paras)}</div>")
def sec_news1():
    n = d['news'][1]
    return f"<h3 style='margin-top:2px'>{n[0]}</h3><div class='cols2' style='font-size:8pt'><p style='margin:0'>{hyph(n[1])}</p></div>"
def sec_word():
    if not d.get('word'): return ''
    w, pos, defn, ex = d['word']
    return (f"<div class='word'><div><div class='wl'>Word of the Day</div><div class='ww'>{w}</div><div class='wp'>{pos}</div></div>"
            f"<div class='wd'>{defn}<br><i style='color:#555'>“{ex}”</i></div></div>")
def sec_joke():
    return (f"<div class='box2'><h3 style='margin:0 0 1px'>Daily Joke</h3><p class='small' style='margin:0'>{d['joke']}</p></div>") if d.get('joke') else ''
def sec_sports():
    parts = []
    if d.get('yday'):
        parts.append("<h3 style='margin-top:0'>" + d.get('yday_title', "Yesterday's Scores") + "</h3><div class='small'>" + ''.join(
            f"<div style='padding:2px 0;border-bottom:1px dotted #aaa'><span class='cap'>{a}</span><br><b style='font-family:PF,serif;font-size:9pt'>{b}</b></div>" for a, b in d['yday']) + "</div>")
    if d.get('lions'): parts.append("<h3>Lions Report</h3><p class='small'>" + d['lions'] + "</p>")
    if d.get('fantasy'): parts.append("<h3>Fantasy Football: Top Performers</h3><ul class='small'>" + li(d['fantasy']) + "</ul>")
    if d.get('tonight'): parts.append("<h3>" + d.get('tonight_title', 'Tonight in Detroit') + "</h3><ul class='small'>" + li(d['tonight']) + "</ul>")
    if d.get('hs'): parts.append("<h3>Seaholm &amp; Groves</h3><ul class='small'>" + li(d['hs']) + "</ul>")
    return ("<h2>Sports Page</h2>" + ''.join(parts)) if parts else ''
def sec_ari_fantasy():
    f = d.get('ari_fantasy')
    if not f: return ''
    return (f"<div class='box2 plain'><h3 style='margin:0 0 1px'>{f.get('title', 'Ari&#8217;s Fantasy Team')}</h3>"
            f"<ul class='small ff'>{li(f.get('items', []))}</ul></div>")
def extra_html(e):
    """One filler item: title + short text (+ source), with an optional real picture (img + credit; README: Photo sources).
    No drawing activities (Jacob, 2026-10-10)."""
    pic = ''
    if e.get('img'):
        from PIL import Image; import io
        im = Image.open(e['img']).convert('RGB'); im.thumbnail((600, 400)); bio = io.BytesIO(); im.save(bio, 'JPEG', quality=82)
        tag = "<span class='illus'>Illustration</span>" if e.get('illus') else ''   # AI art is always labeled (README: AI illustrations)
        pic = (f"<div style='position:relative;border:1px solid #161410;line-height:0;margin:1px 0 1px'><img src='data:image/jpeg;base64,{base64.b64encode(bio.getvalue()).decode()}' "
               f"style='width:100%;height:auto;max-height:{int(e.get('img_h', 130))}px;object-fit:cover'>{tag}</div>")
    return f"<div class='box2'><h3 style='margin:0 0 1px'>{e['title']}</h3>{pic}<p class='small' style='margin:0'>{e['text']}</p></div>"
_extras = d.get('extras') or []
_placed_extras = set()
def sec_extra(i):
    if i >= len(_extras): return ''
    _placed_extras.add(i)
    return extra_html(_extras[i])
def sec_extras():
    return ''.join(extra_html(e) for i, e in enumerate(_extras) if i not in _placed_extras)
def team_box(key, default_title):
    """A kid's team box (mda, spartans), copied from state by the daily run: pro-schedule game cards (.gm-*)."""
    m = d.get(key)
    if not m or not m.get('items'): return ''
    return (f"<div class='box2 sport'><h3 style='margin:0 0 1px'>{m.get('title', default_title)}</h3>"
            f"<ul class='small ff'>{li(m['items'])}</ul></div>")
def sec_mda(): return team_box('mda', 'MDA Kicks &amp; Giggles')
def sec_spartans(): return team_box('spartans', 'Spartans Hoop Scoop')
def sec_news0():
    return '' if d.get('fantasy') or not d.get('news') else story(*d['news'][0])
# Featured artwork: a family kid's own art, framed like a gallery piece (Jacob, 2026-10-14; README: Featured artwork).
# edition.json `featured_art`, or else the entry in featured/queue.json whose date falls in this edition's date(s).
if not d.get('featured_art') and os.path.exists(os.path.join(_KIT, 'featured', 'queue.json')):
    _due = [e for e in json.load(open(os.path.join(_KIT, 'featured', 'queue.json'))) if e.get('date') in edition_days()]
    if _due:
        d['featured_art'] = dict(_due[0], img=os.path.join(_KIT, _due[0]['img']))
if d.get('featured_art'):
    print(f"FEATURED: {d['featured_art']['title']} by {d['featured_art']['artist']}", file=sys.stderr)
def sec_featured():
    a = d.get('featured_art')
    if not a or not a.get('img'): return ''
    from PIL import Image; import io
    im = Image.open(a['img']).convert('RGB'); im.thumbnail((700, 900)); bio = io.BytesIO(); im.save(bio, 'JPEG', quality=86)
    note = f"<p class='fa-note'>{a['note']}</p>" if a.get('note') else ''
    return (f"<div class='featured'><div class='fa-frame'><img src='data:image/jpeg;base64,{base64.b64encode(bio.getvalue()).decode()}'></div>"
            f"<div class='fa-card'><div class='fa-kicker'>Featured Artwork</div><div class='fa-title'>{a['title']}</div>"
            f"<div class='fa-by'>by {a['artist']}</div>{note}</div></div>")
# Monday NFL page: Sunday's final scores as scoreboard tiles, a few highlights, and the Monday Night Football
# preview (Jacob, 2026-10-19; README: Monday NFL page). edition.json `nfl_sunday`; Mondays in the NFL season only.
def sec_nfl():
    n = d.get('nfl_sunday')
    if not n: return ''
    def tile(a, sa, b, sb):
        row = lambda t, x, win: f"<div class='nt-row{' nt-win' if win else ''}'><span>{t}</span><span>{x}</span></div>"
        return f"<div class='nt'>{row(a, sa, sa > sb)}{row(b, sb, sb > sa)}</div>"
    parts = []
    if n.get('scores'):
        parts.append("<h3 style='margin:0 0 2px'>" + n.get('title', 'NFL Sunday') + "</h3><div class='nfl-grid'>"
                     + ''.join(tile(*g) for g in n['scores']) + "</div>")
    if n.get('highlights'):
        parts.append("<ul class='small nfl-hl'>" + li(n['highlights']) + "</ul>")
    for m in n.get('mnf') or []:
        parts.append(f"<div class='mnf'><div class='gm-when'>Monday Night Football · {m['when']}</div>"
                     f"<div class='mnf-game'>{m['game']}</div><p class='small' style='margin:0'>{m['text']}</p></div>")
    return f"<div class='box2 plain nfl'>{''.join(parts)}</div>" if parts else ''
# Daily puzzle (Jacob, 2026-10-19): the crossword (4-5 answers about the day's paper, laid out and checked by
# crossword.py) on Mon/Wed/Fri, and a 4x4 sudoku made from the date by sudoku.py on Tue/Thu/Sat (Weekend Edition).
# How-to-play instructions print with the sudoku for its first two weeks.
SUDOKU_DAYS = {1, 3, 5}              # Tue, Thu, Sat
SUDOKU_HOW_TO_UNTIL = '2026-11-02'   # first sudoku 2026-10-20, instructions for two weeks
def puzzle_kind():
    days = edition_days()
    if not days: return 'crossword'
    import datetime as _dt
    return 'sudoku' if _dt.date.fromisoformat(days[0]).weekday() in SUDOKU_DAYS else 'crossword'
_puzzle_done = []
def sec_puzzle():
    if _puzzle_done: return ''          # placed once, whichever name the layout uses
    _puzzle_done.append(1)
    if puzzle_kind() == 'sudoku':
        day = edition_days()[0]
        print(f"PUZZLE: sudoku{' with how-to' if day <= SUDOKU_HOW_TO_UNTIL else ''}", file=sys.stderr)
        return sudoku.html_box(day, how_to=day <= SUDOKU_HOW_TO_UNTIL)
    if not d.get('crossword'):
        print("CROSSWORD WARNING: today is a crossword day but edition.json has no 'crossword'", file=sys.stderr)
        return ''
    box, warn = crossword.html_box(d['crossword'])
    print(warn or "PUZZLE: crossword", file=sys.stderr)
    return box
SECTIONS = {'puzzle': sec_puzzle, 'crossword': sec_puzzle, 'sudoku': sec_puzzle, 'nfl': sec_nfl, 'featured': sec_featured, 'schedule': sec_schedule, 'week': sec_week, 'school_notes': sec_school_notes, 'left_story': sec_left_story,
            'lead': sec_lead, 'news1': sec_news1, 'word': sec_word, 'joke': sec_joke, 'sports': sec_sports, 'ari_fantasy': sec_ari_fantasy, 'mda': sec_mda, 'spartans': sec_spartans, 'news0': sec_news0}
BOXED = {'week', 'word', 'joke', 'ari_fantasy', 'mda', 'spartans', 'featured', 'nfl', 'puzzle', 'crossword', 'sudoku'}

# Layout: flexible column count, widths and placement (README: readability first). Default = the approved 3-column page.
DEFAULT_LAYOUT = {'columns': [
    {'width': '1.85in', 'sections': ['schedule', 'week', 'school_notes', 'left_story']},
    {'width': '3.95in', 'sections': ['lead', 'news1', 'word', 'joke']},
    {'width': '2.1in', 'sections': ['ari_fantasy', 'spartans', 'mda', 'sports', 'news0']}]}
layout = d.get('layout') or DEFAULT_LAYOUT
for c in layout['columns']:
    for name in c['sections']:
        if name not in SECTIONS and not name.startswith('extra:') and name != 'extras':
            raise SystemExit(f"layout: unknown section '{name}' (known: {', '.join(SECTIONS)})")
# The day's puzzle is never dropped: if the layout doesn't place it, it goes right under the joke.
if not {'puzzle', 'crossword', 'sudoku'} & {n for c in layout['columns'] for n in c['sections']}:
    layout = json.loads(json.dumps(layout))
    for c in layout['columns']:
        if 'joke' in c['sections']: c['sections'].insert(c['sections'].index('joke') + 1, 'puzzle'); break
    else:
        layout['columns'][-1]['sections'].append('puzzle')
# The Monday NFL page is never dropped: if the layout doesn't place it, it goes right above the Sports Page.
if d.get('nfl_sunday') and 'nfl' not in [n for c in layout['columns'] for n in c['sections']]:
    layout = json.loads(json.dumps(layout))
    for c in layout['columns']:
        if 'sports' in c['sections']: c['sections'].insert(c['sections'].index('sports'), 'nfl'); break
    else:
        layout['columns'][-1]['sections'].append('nfl')
# A due featured artwork is never dropped: if the layout doesn't place it, it goes right under the headline story.
if d.get('featured_art') and 'featured' not in [n for c in layout['columns'] for n in c['sections']]:
    layout = json.loads(json.dumps(layout))
    for c in layout['columns']:
        if 'lead' in c['sections']: c['sections'].insert(c['sections'].index('lead') + 1, 'featured')
placed = [n for c in layout['columns'] for n in c['sections']]
missing = [n for n in ('lead', 'word') if n not in placed]
if missing:
    raise SystemExit(f"layout: required sections not placed: {missing}")
def render_section(n):
    if n.startswith('extra:'): return sec_extra(int(n.split(':', 1)[1]))
    if n == 'extras': return sec_extras()
    return SECTIONS[n]()
def column(names):
    out, prev_boxed = [], True
    for n in names:
        h = render_section(n)
        if not h: continue
        if out and not prev_boxed and n not in BOXED and not n.startswith('extra'): out.append("<div class='rule'></div>")
        out.append(h); prev_boxed = n in BOXED or n.startswith('extra') 
    return f"<div class='col'>{''.join(out)}</div>"
grid = ' '.join(c['width'] for c in layout['columns'])
# Explicit extra:N placements render first so a column holding 'extras' only gets the leftovers.
for c in layout['columns']:
    for n in c['sections']:
        if n.startswith('extra:'): _placed_extras.add(int(n.split(':', 1)[1]))
body_html = ''.join(column(c['sections']) for c in layout['columns'])

# Comic strip: composed from the art.py character library by edition.json `comic` (README: Comic).
if not d.get('comic'):
    print("COMIC WARNING: edition.json has no 'comic'; printing the sample strip, which repeats. Write a new one.", file=sys.stderr)
comic_html = art.comic(d.get('comic'))

# No sources inside the page: they are credited only in the small footer (Jacob, 2026-10-12).
for k in ('wx', 'wx2'):
    d[k] = re.sub(r'\s*\((?:NWS|National Weather Service)\)', '', d.get(k) or '')
_credits = []
if d.get('head_photo', {}).get('credit') and hp_b64: _credits.append(f"Headline photo: {d['head_photo']['credit']}")
if d.get('critter', {}).get('credit') and d['critter'].get('img'): _credits.append(f"{d['critter'].get('name', 'Critter')} photo: {d['critter']['credit']}")
_credits += [f"{e['title'].split(':')[0]}: {e['credit']}" for e in _extras if e.get('img') and e.get('credit') and not e.get('illus')]
if any(e.get('img') and e.get('illus') for e in _extras): _credits.append("Illustrations labeled “Illustration” are AI-generated with Grok (xAI)")
# Painted characters (library) or painted backdrops: credit Grok, and the footer's "comic is original" covers only the characters.
_painted_cast = art.COMIC_STATS['painted'] > 0          # set by art.comic() above
if _painted_cast or art.uses_painted(d.get('comic')):
    _credits.append("Comic " + ("art" if _painted_cast and art.uses_painted(d.get('comic')) else "characters" if _painted_cast else "backgrounds")
                    + " painted with Grok (xAI)" + (" from the original character designs" if _painted_cast else ""))
    d['foot'] = re.sub(r'\b([Cc]omic) (?:is|are) original', r'\1 characters are original', d['foot'])
# One run-on line, no breaks, so the footer takes as little room as possible (Jacob, 2026-10-13).
foot_html = re.sub(r'\s*<br\s*/?>\s*', ' · ', d['foot'].strip()) + (f" · Pictures: {' · '.join(_credits)}" if _credits else '')

# Top strip: weather, plus the lunch box only when there is lunch to show (none on weekend editions).
has_lunch = bool(d.get('lunch'))
strip_grid = '1.6fr 1fr' if has_lunch else '1fr'
lunch_title = d.get('lunch_title', "Today's School Lunch")
lunch_html = (f"<div class='box'><h2>{lunch_title} · Quarton</h2><div class='lunch'>{d['lunch']}</div></div>") if has_lunch else ''
banner_html = (f"<div class='banner'>{''.join(f'<span>{b}</span>' for b in d['banner'])}</div>") if d.get('banner') else ''
html=f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>The Fairfax Daily Scoop — {d['date']}</title><style>
@font-face{{font-family:Frak;src:url(data:font/woff2;base64,{frak}) format('woff2');font-weight:700}}
@font-face{{font-family:PF;src:url(data:font/woff2;base64,{pf4}) format('woff2');font-weight:400}}
@font-face{{font-family:PF;src:url(data:font/woff2;base64,{pf7}) format('woff2');font-weight:700}}
@font-face{{font-family:LB;src:url(data:font/woff2;base64,{lb4}) format('woff2');font-weight:400}}
@font-face{{font-family:LB;src:url(data:font/woff2;base64,{lb7}) format('woff2');font-weight:700}}
@page{{size:Letter;margin:0.3in}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:LB,serif;font-size:7.8pt;line-height:1.3;color:#161410}}
.page{{width:7.9in;height:10.4in;overflow:hidden;display:flex;flex-direction:column}}
.mast{{text-align:center;border-bottom:3px double #161410;padding-bottom:2px}}
.title{{font-family:Frak,serif;font-size:50pt;font-weight:700;line-height:1}}
/* The paper's official icon, an ice cream cone (art.py scoop_icon), on both sides of the title (Jacob, 2026-10-13) */
.titlerow{{display:flex;align-items:center;justify-content:center;gap:14px}}
.ears{{display:flex;justify-content:space-between;font-family:PF,serif;font-size:7.2pt;border-top:1px solid #161410;border-bottom:1px solid #161410;padding:2px 4px;margin-top:3px;text-transform:uppercase;letter-spacing:.6px}}
.strip{{display:grid;grid-template-columns:{strip_grid};border-bottom:1px solid #161410}}
.box{{padding:3px 7px}} .box+.box{{border-left:1px solid #161410}}
h2{{font-family:PF,serif;font-weight:700;font-size:9.2pt;text-transform:uppercase;letter-spacing:.8px;border-bottom:1px solid #161410;margin-bottom:3px;padding-bottom:1px}}
h3{{font-family:PF,serif;font-weight:700;font-size:10.8pt;line-height:1.12;margin:4px 0 2px}}
.big{{font-family:PF,serif;font-weight:700;font-size:22pt;line-height:1}}
/* Weather icons from art.py, picked from the NWS wording (Jacob, 2026-10-12) */
.wxi{{flex:none;display:block}}
.fc{{flex:1;display:flex;align-items:center;justify-content:center;gap:3px;border:1px solid #161410;padding:1px 2px;line-height:1.15;text-align:center}}
.body{{flex:1;display:grid;grid-template-columns:{grid};min-height:0}}
.col{{padding:3px 6px;overflow:hidden;min-height:0}} .col+.col{{border-left:1px solid #161410}}
ul{{list-style:none}} .sched li{{padding:3px 0;border-bottom:1px dotted #8a8478}}
.cap{{font-style:italic;font-size:6.9pt;color:#555;margin-bottom:2px}}
p{{margin-bottom:3px;text-align:justify;hyphens:auto}}
.small{{font-size:7.7pt;line-height:1.26}}
.rule{{border-top:1px solid #161410;margin:4px 0}}
.box2{{background:#efe9d8;border:1px solid #161410;padding:3px 5px;margin-top:4px}}
/* Featured artwork: gallery frame + museum title card (Jacob, 2026-10-14) */
.featured{{display:flex;flex-wrap:wrap;justify-content:center;gap:10px;align-items:center;margin-top:5px;padding:6px;border:1px solid #161410;background:#fbf7ec}}
.fa-frame{{flex:0 0 auto;padding:5px;background:#c9a34a;border:1px solid #161410;box-shadow:inset 0 0 0 2px #e9d397}}
.fa-frame img{{display:block;height:196px;width:auto;border:3px solid #fff;outline:1px solid #8a6d28}}
.fa-card{{flex:1 1 150px;text-align:center}}
.fa-kicker{{font-family:PF,serif;font-weight:700;font-size:8.4pt;text-transform:uppercase;letter-spacing:1.4px;border-top:1px solid #161410;border-bottom:1px solid #161410;padding:1px 0;margin-bottom:6px}}
.fa-title{{font-family:PF,serif;font-style:italic;font-weight:700;font-size:16pt;line-height:1.1}}
.fa-by{{font-family:PF,serif;font-size:10pt;margin:3px 0 6px}}
.fa-note{{font-size:7.8pt;line-height:1.3;margin:0}}
.headline{{font-family:PF,serif;font-weight:700;font-size:20pt;line-height:1.02;text-align:center;margin:2px 0 2px}}
.sub{{font-style:italic;text-align:center;font-size:8.6pt;margin-bottom:4px}}
.cols2{{column-count:2;column-gap:9px;column-rule:1px solid #bbb;font-size:8.2pt}}
.cols2 p:first-child::first-letter{{font-family:PF,serif;font-weight:700;font-size:20pt;float:left;line-height:.85;padding-right:2px}}
.comic{{border:2px solid #161410;padding:2px 3px;margin:2px 0 3px}}
.ct{{font-family:PF,serif;font-weight:700;letter-spacing:2px;text-align:center;font-size:9pt;margin-bottom:2px}}
.cg{{display:grid;grid-template-columns:repeat(4,1fr);gap:3px}}
.foot{{border-top:3px double #161410;font-size:6.2pt;line-height:1.2;text-align:center;padding-top:2px;color:#444}}
/* School lunch: large and bold, no source line (Jacob, 2026-10-12) */
.lunch{{font-weight:700;font-family:PF,serif;font-size:11pt;line-height:1.25}}
.lunch span{{display:block;line-height:1.3;margin-top:2px}}
.illus{{position:absolute;right:3px;bottom:3px;line-height:1;background:#fff;border:1px solid #161410;font-size:5.8pt;letter-spacing:.6px;text-transform:uppercase;padding:1px 3px}}
.banner{{text-align:center;font-family:PF,serif;font-weight:700;font-size:10.5pt;letter-spacing:.6px;padding:3px 4px;border-bottom:1px solid #161410;background:#f6ecd2}}
.banner span+span::before{{content:"  ·  ";font-weight:400}}
.ff li{{padding:2px 0;border-bottom:1px dotted #b9ad8c}} .ff li:last-child{{border-bottom:0}}
/* Kids' team boxes have their own shade; Detroit sports and Ari's fantasy box have none (Jacob, 2026-10-10) */
/* Daily Crossword (Jacob, 2026-10-19): grid beside the clues; answers upside down at the bottom */
.xw{{background:#fff}} .xw-body{{display:flex;flex-wrap:wrap;gap:8px;align-items:flex-start}} .xw-grid{{flex:0 1 auto;max-width:100%;height:auto}}
.xw-clues{{flex:1 1 120px;font-size:7.6pt;line-height:1.28}} .xw-h{{font-family:PF,serif;font-weight:700;font-size:7.4pt;text-transform:uppercase;letter-spacing:.8px;margin-top:1px}}
.xw-list{{list-style:none;margin:0 0 2px}} .xw-list b{{font-family:PF,serif}}
.sd-grid{{flex:0 0 auto}} .sd-how{{flex:1 1 120px;font-size:7.6pt;line-height:1.3;margin:0;text-align:left}}
.xw-key{{transform:rotate(180deg);font-size:6.2pt;color:#555;text-align:center;margin-top:3px}}
/* Monday NFL page (Jacob, 2026-10-19): scoreboard tiles, winner bold */
.nfl{{padding:3px 3px}} .nfl-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(76px,1fr));gap:2px}}
.nt{{border:1px solid #161410;padding:1px 3px;font-size:7.1pt;line-height:1.25}}
.nt-row{{display:flex;justify-content:space-between;gap:3px}} .nt-row span:last-child{{font-family:PF,serif;font-size:8.6pt}} .nt-win{{font-weight:700}}
.nfl-hl{{margin:3px 0 0}} .mnf{{border-top:1px solid #161410;margin-top:4px;padding-top:3px}} .mnf .gm-when{{color:#161410}}
.mnf-game{{font-family:PF,serif;font-weight:700;font-size:10pt;line-height:1.15}}
/* Headline icon badge when there is no photo (Jacob, 2026-10-19) */
.hi-float{{float:right;margin:1px 0 2px 6px}}
.hi-badge{{width:58px;height:58px;border-radius:50%;border:1.5px solid #161410;background:#fbf7ec;display:flex;align-items:center;justify-content:center;box-shadow:inset 0 0 0 3px #fff,inset 0 0 0 4px #c9b88a}}
.sport{{background:#dcebd6}} .sport .ff li{{border-bottom-color:#8fae86}} .plain{{background:#fff}}
.gm-when{{display:block;font-family:PF,serif;font-weight:700;font-size:6.9pt;text-transform:uppercase;letter-spacing:.8px;color:#2f5d2a}}
.gm-match{{display:block;font-family:PF,serif;font-weight:700;font-size:9.4pt;line-height:1.15}}
.gm-loc{{display:block;font-style:italic;font-size:7.3pt}}
.gm-extra{{display:block;font-size:7.3pt;color:#333}}
.gm-recap{{display:block;font-size:7.3pt;line-height:1.2;text-align:justify;hyphens:auto;margin-top:2px;padding-top:2px;border-top:1px dotted #9bb596}}
.word{{border:2px solid #161410;background:#fff7e0;padding:4px 7px;margin-top:5px;display:flex;gap:9px;align-items:center}}
.word .wl{{font-family:PF,serif;font-size:7pt;text-transform:uppercase;letter-spacing:1.2px;color:#7a2e1f}}
.word .ww{{font-family:PF,serif;font-weight:700;font-size:23pt;line-height:1;color:#7a2e1f}}
.word .wp{{font-style:italic;font-size:7.4pt;color:#555}}
.word .wd{{font-size:8.2pt;line-height:1.28;border-left:1px solid #c9b88a;padding-left:9px;flex:1}}
</style></head><body><div class="page">
<div class="mast"><div class="titlerow">{art.scoop_icon(58)}<div class="title">The Fairfax Daily Scoop</div>{art.scoop_icon(58, flip=True)}</div>
<div class="ears"><span>Birmingham, Michigan</span><span>{d['date']}</span><span>{d.get('edition', 'Daily Edition')} · Est. 2026</span></div></div>
{banner_html}
<div class="strip">
 <div class="box"><h2>Weather · Birmingham</h2><div style="display:flex;gap:8px;align-items:center">{art.weather_icon(art.wx_kind(d['wx']), 38)}<div class="big">{d['hi']}°</div><div>{d['wx']}<br><span class="cap">{d['wx2']}</span></div></div>
 <div style="display:flex;gap:4px;margin-top:3px">{''.join(f"<div class='fc'>{art.weather_icon(art.wx_kind(e), 26)}<div><b style='font-family:PF,serif'>{a}</b><br><b>{b}°</b> / {c}°<br><span class='cap' style='margin:0'>{e}</span></div></div>" for a,b,c,e in d['forecast'])}</div></div>
 {lunch_html}
</div>
<div class="body">{body_html}</div>
{comic_html}
<div class="foot">{foot_html}</div></div></body></html>"""
open('gazette.html','w').write(html)
