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
.strip{{display:grid;grid-template-columns:1.6fr 1fr;border-bottom:1px solid #161410}}
.box{{padding:3px 7px}} .box+.box{{border-left:1px solid #161410}}
h2{{font-family:PF,serif;font-weight:700;font-size:9.2pt;text-transform:uppercase;letter-spacing:.8px;border-bottom:1px solid #161410;margin-bottom:3px;padding-bottom:1px}}
h3{{font-family:PF,serif;font-weight:700;font-size:10.8pt;line-height:1.12;margin:4px 0 2px}}
.big{{font-family:PF,serif;font-weight:700;font-size:22pt;line-height:1}}
.body{{flex:1;display:grid;grid-template-columns:1.85in 3.95in 2.1in;min-height:0}}
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
</style></head><body><div class="page">
<div class="mast"><div class="title">The Fairfax Daily Scoop</div>
<div class="ears"><span>Birmingham, Michigan</span><span>{d['date']}</span><span>Daily Edition · Est. 2026</span></div></div>
<div class="strip">
 <div class="box"><h2>Weather · Birmingham</h2><div style="display:flex;gap:8px;align-items:center"><div class="big">{d['hi']}°</div><div>{d['wx']}<br><span class="cap">{d['wx2']}</span></div></div>
 <div style="display:flex;gap:4px;margin-top:3px">{''.join(f"<div style='flex:1;text-align:center;border:1px solid #161410;padding:1px 0;line-height:1.15'><b style='font-family:PF,serif'>{a}</b><br><b>{b}°</b> / {c}°<br><span class='cap' style='margin:0'>{e}</span></div>" for a,b,c,e in d['forecast'])}</div></div>
 <div class="box"><h2>Today's School Lunch · Quarton</h2><div style="font-weight:700;font-family:PF,serif;font-size:8.6pt">{d['lunch']}</div><div class="cap">{d['lunch_src']}</div></div>
</div>
<div class="body">
 <div class="col"><h2>The Family Schedule</h2><ul class="sched small">{li(d['sched'])}</ul>
  <div class="cap" style="margin-top:2px">{d['sched_note']}</div>
  <div class="box2"><h2 style="border:0;margin:0">Coming Up</h2><ul class="small">{li(d['week'])}</ul></div>
  <div class="rule"></div><h2>Quarton Notes</h2><ul class="small">{li(d['quarton'])}</ul>
  <div class="rule"></div>{(f"<h2>Cutest Critter</h2><div style='border:1px solid #161410;line-height:0'><img src='data:image/jpeg;base64,{crit_b64}' style='width:100%;height:auto;max-height:150px;object-fit:cover'></div><div class='cap' style='text-align:center'><b>{d['critter']['name']}</b> — {d['critter']['fact']} <i>Photo: {d['critter'].get('credit','')}</i></div>") if d.get('critter') else story(*d['news'][2])}
 </div>
 <div class="col">
  <div class="headline">{d['head']}</div><div class="sub">{d['sub']}</div>
  {head_photo_html}
  <div class="cols2">{''.join(f'<p>{x}</p>' for x in d['story'])}</div><div class="cap">{d['head_src']}</div>
  <div class="rule"></div><h3 style="margin-top:2px">{d['news'][1][0]}</h3><div class="cols2" style="font-size:8pt"><p style="margin:0">{d['news'][1][1]}</p></div><div class="cap">{d['news'][1][2]}</div>
  <div class="box2"><h3 style="margin:0 0 1px">Word of the Day: {d['word'][0]}</h3><p class="small" style="margin:0"><i>{d['word'][1]}</i> — {d['word'][2]} <span class="cap" style="font-style:italic">“{d['word'][3]}”</span></p></div>
  <div class="box2" style="display:flex;gap:8px"><div style="flex:1"><h3 style="margin:0 0 1px">Daily Riddle</h3><p class="small" style="margin:0">{d['riddle']}<br><span class="cap" style="font-style:normal">{d['riddle_prev']}</span></p></div><div style="flex:1;border-left:1px solid #161410;padding-left:8px"><h3 style="margin:0 0 1px">Daily Joke</h3><p class="small" style="margin:0">{d['joke']}</p></div></div>
  </div>
 <div class="col"><h2>Sports Page</h2>
  {("<h3 style='margin-top:0'>Yesterday's Scores</h3><div class='small'>"+''.join(f"<div style='padding:2px 0;border-bottom:1px dotted #aaa'><span class='cap'>{a}</span><br><b style='font-family:PF,serif;font-size:9pt'>{b}</b></div>" for a,b in d['yday'])+"</div>") if d.get('yday') else ""}
  {("<h3>Lions Report</h3><p class='small'>"+d['lions']+"</p>") if d.get('lions') else ""}
  {("<h3>Fantasy Football: Top Performers</h3><ul class='small'>"+li(d['fantasy'])+"</ul>") if d.get('fantasy') else ""}
  {("<h3>Tonight in Detroit</h3><ul class='small'>"+li(d['tonight'])+"</ul>") if d.get('tonight') else ""}
  {("<h3>Seaholm &amp; Groves</h3><ul class='small'>"+li(d['hs'])+"</ul>") if d.get('hs') else ""}
  {"" if d.get('fantasy') else "<div class='rule'></div>"+story(*d['news'][0])}
 </div>
</div>
{art.comic()}
<div class="foot">{d['foot']}</div></div></body></html>"""
open('gazette.html','w').write(html)
