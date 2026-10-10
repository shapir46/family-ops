# Original illustrations (SVG strings) -- no third-party characters or photos
def bubble(x,y,w,lines,tail=(0,0)):
    h=10*len(lines)+8
    t=''.join(f'<text x="{x+w/2}" y="{y+13+i*10}" text-anchor="middle" font-size="8.2" font-family="LB" fill="#161410">{l}</text>' for i,l in enumerate(lines))
    tx,ty=tail
    return f'''<g><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="#fff" stroke="#161410" stroke-width="1.3"/>
<polygon points="{tx-4},{y+h-1} {tx+4},{y+h-1} {tx},{ty}" fill="#fff" stroke="#161410" stroke-width="1.3"/>
<rect x="{tx-3.5}" y="{y+h-2.5}" width="7" height="3.5" fill="#fff"/>{t}</g>'''

def pbear(x,y,s=1,scarf=False,beanie=False):
    f=f'translate({x},{y}) scale({s},{s})'
    sc='<path d="M-20 18 Q0 30 20 18 L20 25 Q0 37 -20 25 Z" fill="#c9443b"/><rect x="10" y="22" width="9" height="20" rx="3" fill="#c9443b"/><line x1="12" y1="36" x2="17" y2="36"/>' if scarf else ''
    bn='<path d="M-22 -8 Q0 -38 22 -8 Z" fill="#3b6fb6"/><rect x="-23" y="-10" width="46" height="5" rx="2.5" fill="#2c5489"/><circle cx="0" cy="-27" r="5" fill="#fbfaf3"/>' if beanie else ''
    return f'''<g transform="{f}" stroke="#161410" stroke-width="1.5" stroke-linejoin="round">
<ellipse cx="0" cy="38" rx="30" ry="27" fill="#fbfaf3"/><ellipse cx="-14" cy="62" rx="10" ry="6" fill="#f1efe4"/><ellipse cx="14" cy="62" rx="10" ry="6" fill="#f1efe4"/>
<circle cx="-18" cy="-14" r="8" fill="#fbfaf3"/><circle cx="18" cy="-14" r="8" fill="#fbfaf3"/><circle cx="-18" cy="-14" r="3.5" fill="#e8e2d0" stroke="none"/><circle cx="18" cy="-14" r="3.5" fill="#e8e2d0" stroke="none"/>
<ellipse cx="0" cy="0" rx="24" ry="21" fill="#fbfaf3"/>
<ellipse cx="0" cy="8" rx="11" ry="8" fill="#f1efe4"/>
<circle cx="-9" cy="-4" r="2.4" fill="#161410" stroke="none"/><circle cx="9" cy="-4" r="2.4" fill="#161410" stroke="none"/>
<ellipse cx="0" cy="4" rx="4" ry="2.8" fill="#161410"/><path d="M0 7 L0 10 M-5 12 Q0 15 5 12" fill="none"/>
<ellipse cx="-14" cy="5" rx="3.5" ry="2" fill="#f6c9c0" stroke="none"/><ellipse cx="14" cy="5" rx="3.5" ry="2" fill="#f6c9c0" stroke="none"/>{sc}{bn}</g>'''

def afox(x,y,s=1,flip=False,muffs=False):
    f=f'translate({x},{y}) scale({-s if flip else s},{s})'
    mf='<path d="M-17 -2 Q0 -22 17 -2" fill="none" stroke="#555" stroke-width="2"/><circle cx="-17" cy="2" r="6" fill="#d9534f"/><circle cx="17" cy="2" r="6" fill="#d9534f"/>' if muffs else ''
    return f'''<g transform="{f}" stroke="#161410" stroke-width="1.4" stroke-linejoin="round">
<path d="M-18 40 Q-52 36 -50 8 Q-46 -6 -36 4 Q-30 24 -14 28 Z" fill="#fdfdfa"/>
<ellipse cx="0" cy="34" rx="18" ry="17" fill="#f3f1e8"/>
<ellipse cx="-7" cy="50" rx="6" ry="3.5" fill="#6d7c8c"/><ellipse cx="7" cy="50" rx="6" ry="3.5" fill="#6d7c8c"/>
<polygon points="-15,-6 -10,-26 -2,-10" fill="#f3f1e8"/><polygon points="15,-6 10,-26 2,-10" fill="#f3f1e8"/>
<polygon points="-11,-9 -10,-20 -5,-11" fill="#a9b8c6" stroke="none"/><polygon points="11,-9 10,-20 5,-11" fill="#a9b8c6" stroke="none"/>
<ellipse cx="0" cy="4" rx="17" ry="14" fill="#f3f1e8"/>
<circle cx="-6" cy="1" r="2" fill="#161410" stroke="none"/><circle cx="6" cy="1" r="2" fill="#161410" stroke="none"/>
<ellipse cx="0" cy="8" rx="2.6" ry="2" fill="#161410"/><path d="M-3 11 Q0 14 3 11" fill="none"/>{mf}</g>'''

def ipanel(inner,bg="#dcecf6"):
    return f'''<svg viewBox="0 0 200 122" width="100%" xmlns="http://www.w3.org/2000/svg"><rect x="1" y="1" width="198" height="120" fill="{bg}" stroke="#161410" stroke-width="2"/>
<path d="M1 98 Q50 90 100 97 T199 95 L199 121 L1 121 Z" fill="#f4f9fc" stroke="#161410" stroke-width="1"/>
<g fill="#fff" opacity=".9"><circle cx="30" cy="22" r="1.6"/><circle cx="120" cy="14" r="1.6"/><circle cx="170" cy="40" r="1.6"/><circle cx="85" cy="40" r="1.3"/></g>{inner}</svg>'''

def fpanel(inner,bg="#fbe4c6",boot=False,tug=False):
    """Ice-fishing scene: dusk sky, low sun, flat blue ice, hole in the ice."""
    return f'''<svg viewBox="0 0 200 122" width="100%" xmlns="http://www.w3.org/2000/svg"><rect x="1" y="1" width="198" height="120" fill="{bg}" stroke="#161410" stroke-width="2"/>
<circle cx="172" cy="84" r="14" fill="#f6b25c" opacity=".85"/>
<path d="M1 90 L199 90 L199 121 L1 121 Z" fill="#cfe3ef" stroke="#161410" stroke-width="1"/>
<path d="M10 100 L40 96 M150 108 L190 104 M70 114 L100 111" stroke="#9fbfd2" stroke-width="1" fill="none"/>
<ellipse cx="112" cy="104" rx="20" ry="6" fill="#3f6f98" stroke="#161410" stroke-width="1.2"/>
{inner}</svg>'''

def comic():
    # Oct 8: ice-fishing gag. New setting (dusk ice lake), new props (rod, boot), beanie + earmuffs.
    rod=lambda tip: f'<line x1="80" y1="76" x2="{tip[0]}" y2="{tip[1]}" stroke="#7a5a35" stroke-width="2"/><line x1="{tip[0]}" y1="{tip[1]}" x2="112" y2="103" stroke="#161410" stroke-width=".8"/>'
    B=lambda: pbear(58,52,.8,False,True)
    F=lambda: afox(158,60,.85,True,True)
    boot='<path d="M104 90 L104 74 L118 74 L118 84 L130 88 L130 94 L104 94 Z" fill="#8a5a2b" stroke="#161410" stroke-width="1.2"/><rect x="104" y="72" width="14" height="4" fill="#5e3b18" stroke="#161410" stroke-width="1"/>'
    p1=fpanel(B()+F()+rod((128,40))+bubble(76,4,116,["Caught anything,","Big Bear?"],tail=(156,52)))
    p2=fpanel(B()+F()+rod((128,40))+bubble(6,2,92,["Not yet. I'm waiting","for a big one."],tail=(58,46)),bg="#fadcb4")
    p3=fpanel(B()+F()+rod((128,52))+bubble(6,2,84,["I've got one!","It's HUGE!"],tail=(58,46)),bg="#f8d3a2")
    p4=fpanel(B()+F()+rod((128,40))+boot+bubble(4,2,52,["A BOOT?"],tail=(56,46))+bubble(76,4,116,["Size 12! Very","fashionable."],tail=(156,52)),bg="#fbe4c6")
    return f'<div class="comic"><div class="ct">ARTIC &amp; BIG BEAR</div><div class="cg">{p1}{p2}{p3}{p4}</div></div>'
