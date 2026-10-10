import base64, glob, json
import art
import os
G=os.environ.get("FONTDIR","./fonts")
def f(p): return base64.b64encode(open(glob.glob(p)[0],'rb').read()).decode()
frak=f(f"{G}/fontsource-grenze-gotisch*/package/files/grenze-gotisch-latin-700-normal.woff2")
pf4=f(f"{G}/fontsource-playfair-display*/package/files/playfair-display-latin-400-normal.woff2")
pf7=f(f"{G}/fontsource-playfair-display*/package/files/playfair-display-latin-700-normal.woff2")
lb4=f(f"{G}/fontsource-libre-baskerville*/package/files/libre-baskerville-latin-400-normal.woff2")
lb7=f(f"{G}/fontsource-libre-baskerville*/package/files/libre-baskerville-latin-700-normal.woff2")
d=json.load(open('edition.json'))
crit_b64=''
if d.get('critter') and d['critter'].get('img'):
    from PIL import Image; import io
    im=Image.open(d['critter']['img']).convert('RGB'); im.thumbnail((500,400)); bio=io.BytesIO(); im.save(bio,'JPEG',quality=82); crit_b64=base64.b64encode(bio.getvalue()).decode()
hp_b64=''
if d.get('head_photo') and d['head_photo'].get('img'):
    from PIL import Image; import io
    im=Image.open(d['head_photo']['img']).convert('RGB'); im.thumbnail((900,500)); bio=io.BytesIO(); im.save(bio,'JPEG',quality=85); hp_b64=base64.b64encode(bio.getvalue()).decode()
head_photo_html=(f"<div style='border:1px solid #161410;line-height:0'><img src='data:image/jpeg;base64,{hp_b64}' style='width:100%;height:auto;max-height:190px;object-fit:cover'></div><div class='cap' style='text-align:center'>Photo: {d['head_photo'].get('credit','')}</div>") if hp_b64 else ''
li=lambda xs:"".join(f"<li>{x}</li>" for x in xs)
def story(h,t,s,first=False): return f"<h3>{h}</h3><p>{t}</p><div class='cap'>{s}</div>"

# ---- Sections: each returns HTML ('' = omit). The layout below places them. ----
def sec_schedule():
    return (f"<h2>{d.get('sched_title', 'The Family Schedule')}</h2><ul class='sched small'>{li(d.get('sched', []))}</ul>"
            f"<div class='cap' style='margin-top:2px'>{d.get('sched_note', '')}</div>") if d.get('sched') else ''
def sec_week():
    return (f"<div class='box2'><h2 style='border:0;margin:0'>{d.get('week_title', 'Coming Up')}</h2><ul class='small'>{li(d['week'])}</ul></div>") if d.get('week') else ''
def sec_school_notes():
    return (f"<h2>{d.get('notes_title', 'Quarton Notes')}</h2><ul class='small'>{li(d['quarton'])}</ul>") if d.get('quarton') else ''
def sec_left_story():
    if d.get('critter'):
        c = d['critter']
        return (f"<h2>Cutest Critter</h2><div style='border:1px solid #161410;line-height:0'><img src='data:image/jpeg;base64,{crit_b64}' style='width:100%;height:auto;max-height:150px;object-fit:cover'></div>"
                f"<div class='cap' style='text-align:center'><b>{c['name']}</b> — {c['fact']} <i>Photo: {c.get('credit','')}</i></div>")
    return story(*d['news'][2]) if len(d.get('news', [])) > 2 else ''
def sec_lead():
    return (f"<div class='headline'>{d['head']}</div><div class='sub'>{d['sub']}</div>{head_photo_html}"
            f"<div class='cols2'>{''.join(f'<p>{x}</p>' for x in d['story'])}</div><div class='cap'>{d['head_src']}</div>")
def sec_news1():
    n = d['news'][1]
    return f"<h3 style='margin-top:2px'>{n[0]}</h3><div class='cols2' style='font-size:8pt'><p style='margin:0'>{n[1]}</p></div><div class='cap'>{n[2]}</div>"
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
    return (f"<div class='box2'><h3 style='margin:0 0 1px'>{f.get('title', 'Ari&#8217;s Fantasy Team')}</h3>"
            f"<ul class='small ff'>{li(f.get('items', []))}</ul></div>")
def sec_news0():
    return '' if d.get('fantasy') or not d.get('news') else story(*d['news'][0])
SECTIONS = {'schedule': sec_schedule, 'week': sec_week, 'school_notes': sec_school_notes, 'left_story': sec_left_story,
            'lead': sec_lead, 'news1': sec_news1, 'word': sec_word, 'joke': sec_joke, 'sports': sec_sports, 'ari_fantasy': sec_ari_fantasy, 'news0': sec_news0}
BOXED = {'week', 'word', 'joke', 'ari_fantasy'}

# Layout: flexible column count, widths and placement (README: readability first). Default = the approved 3-column page.
DEFAULT_LAYOUT = {'columns': [
    {'width': '1.85in', 'sections': ['schedule', 'week', 'school_notes', 'left_story']},
    {'width': '3.95in', 'sections': ['lead', 'news1', 'word', 'joke']},
    {'width': '2.1in', 'sections': ['ari_fantasy', 'sports', 'news0']}]}
layout = d.get('layout') or DEFAULT_LAYOUT
for c in layout['columns']:
    for name in c['sections']:
        if name not in SECTIONS:
            raise SystemExit(f"layout: unknown section '{name}' (known: {', '.join(SECTIONS)})")
placed = [n for c in layout['columns'] for n in c['sections']]
missing = [n for n in ('lead', 'word') if n not in placed]
if missing:
    raise SystemExit(f"layout: required sections not placed: {missing}")
def column(names):
    out, prev_boxed = [], True
    for n in names:
        h = SECTIONS[n]()
        if not h: continue
        if out and not prev_boxed and n not in BOXED: out.append("<div class='rule'></div>")
        out.append(h); prev_boxed = n in BOXED
    return f"<div class='col'>{''.join(out)}</div>"
grid = ' '.join(c['width'] for c in layout['columns'])
body_html = ''.join(column(c['sections']) for c in layout['columns'])

# Top strip: weather, plus the lunch box only when there is lunch to show (none on weekend editions).
has_lunch = bool(d.get('lunch'))
strip_grid = '1.6fr 1fr' if has_lunch else '1fr'
lunch_title = d.get('lunch_title', "Today's School Lunch")
lunch_html = (f"<div class='box'><h2>{lunch_title} · Quarton</h2><div style='font-weight:700;font-family:PF,serif;font-size:8.6pt'>{d['lunch']}</div><div class='cap'>{d.get('lunch_src','')}</div></div>") if has_lunch else ''
banner_html = (f"<div class='banner'>{''.join(f'<span>{b}</span>' for b in d['banner'])}</div>") if d.get('banner') else ''
html=f"""<!doctype html><html><head><meta charset="utf-8"><title>The Fairfax Daily Scoop — {d['date']}</title><style>
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
.ears{{display:flex;justify-content:space-between;font-family:PF,serif;font-size:7.2pt;border-top:1px solid #161410;border-bottom:1px solid #161410;padding:2px 4px;margin-top:3px;text-transform:uppercase;letter-spacing:.6px}}
.strip{{display:grid;grid-template-columns:{strip_grid};border-bottom:1px solid #161410}}
.box{{padding:3px 7px}} .box+.box{{border-left:1px solid #161410}}
h2{{font-family:PF,serif;font-weight:700;font-size:9.2pt;text-transform:uppercase;letter-spacing:.8px;border-bottom:1px solid #161410;margin-bottom:3px;padding-bottom:1px}}
h3{{font-family:PF,serif;font-weight:700;font-size:10.8pt;line-height:1.12;margin:4px 0 2px}}
.big{{font-family:PF,serif;font-weight:700;font-size:22pt;line-height:1}}
.body{{flex:1;display:grid;grid-template-columns:{grid};min-height:0}}
.col{{padding:3px 6px;overflow:hidden;min-height:0}} .col+.col{{border-left:1px solid #161410}}
ul{{list-style:none}} .sched li{{padding:3px 0;border-bottom:1px dotted #8a8478}}
.cap{{font-style:italic;font-size:6.9pt;color:#555;margin-bottom:2px}}
p{{margin-bottom:3px;text-align:justify;hyphens:auto}}
.small{{font-size:7.7pt;line-height:1.26}}
.rule{{border-top:1px solid #161410;margin:4px 0}}
.box2{{background:#efe9d8;border:1px solid #161410;padding:3px 5px;margin-top:4px}}
.headline{{font-family:PF,serif;font-weight:700;font-size:20pt;line-height:1.02;text-align:center;margin:2px 0 2px}}
.sub{{font-style:italic;text-align:center;font-size:8.6pt;margin-bottom:4px}}
.cols2{{column-count:2;column-gap:9px;column-rule:1px solid #bbb;font-size:8.2pt}}
.cols2 p:first-child::first-letter{{font-family:PF,serif;font-weight:700;font-size:20pt;float:left;line-height:.85;padding-right:2px}}
.comic{{border:2px solid #161410;padding:2px 3px;margin:2px 0 3px}}
.ct{{font-family:PF,serif;font-weight:700;letter-spacing:2px;text-align:center;font-size:9pt;margin-bottom:2px}}
.cg{{display:grid;grid-template-columns:repeat(4,1fr);gap:3px}}
.foot{{border-top:3px double #161410;font-size:6.2pt;text-align:center;padding-top:2px;color:#444}}
.banner{{text-align:center;font-family:PF,serif;font-weight:700;font-size:10.5pt;letter-spacing:.6px;padding:3px 4px;border-bottom:1px solid #161410;background:#f6ecd2}}
.banner span+span::before{{content:"  ·  ";font-weight:400}}
.ff li{{padding:2px 0;border-bottom:1px dotted #b9ad8c}} .ff li:last-child{{border-bottom:0}}
.word{{border:2px solid #161410;background:#fff7e0;padding:4px 7px;margin-top:5px;display:flex;gap:9px;align-items:center}}
.word .wl{{font-family:PF,serif;font-size:7pt;text-transform:uppercase;letter-spacing:1.2px;color:#7a2e1f}}
.word .ww{{font-family:PF,serif;font-weight:700;font-size:23pt;line-height:1;color:#7a2e1f}}
.word .wp{{font-style:italic;font-size:7.4pt;color:#555}}
.word .wd{{font-size:8.2pt;line-height:1.28;border-left:1px solid #c9b88a;padding-left:9px;flex:1}}
</style></head><body><div class="page">
<div class="mast"><div class="title">The Fairfax Daily Scoop</div>
<div class="ears"><span>Birmingham, Michigan</span><span>{d['date']}</span><span>{d.get('edition', 'Daily Edition')} · Est. 2026</span></div></div>
{banner_html}
<div class="strip">
 <div class="box"><h2>Weather · Birmingham</h2><div style="display:flex;gap:8px;align-items:center"><div class="big">{d['hi']}°</div><div>{d['wx']}<br><span class="cap">{d['wx2']}</span></div></div>
 <div style="display:flex;gap:4px;margin-top:3px">{''.join(f"<div style='flex:1;text-align:center;border:1px solid #161410;padding:1px 0;line-height:1.15'><b style='font-family:PF,serif'>{a}</b><br><b>{b}°</b> / {c}°<br><span class='cap' style='margin:0'>{e}</span></div>" for a,b,c,e in d['forecast'])}</div></div>
 {lunch_html}
</div>
<div class="body">{body_html}</div>
{art.comic()}
<div class="foot">{d['foot']}</div></div></body></html>"""
open('gazette.html','w').write(html)
