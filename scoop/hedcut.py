import numpy as np, random, math
from PIL import Image, ImageDraw, ImageFilter
def pumpkin(W=800,H=240):
    im=Image.new('L',(W,H),250); d=ImageDraw.Draw(im)
    for y in range(H): d.line([(0,y),(W,y)],fill=int(215-y*0.2))
    d.ellipse([560,18,680,138],fill=252)  # moon
    d.ellipse([590,40,605,55],fill=225); d.ellipse([625,85,650,110],fill=230)
    d.rectangle([0,205,W,H],fill=90)
    def pk(cx,cy,rx,ry,face=True):
        for dx,v in [(-rx*.55,130),(rx*.55,130),(0,150)]:
            d.ellipse([cx+dx-rx*.55,cy-ry,cx+dx+rx*.55,cy+ry],fill=v)
        d.ellipse([cx-rx*.35,cy-ry,cx+rx*.35,cy+ry],fill=165)
        d.polygon([(cx-8,cy-ry+6),(cx+8,cy-ry+6),(cx+22,cy-ry-30),(cx+4,cy-ry-34)],fill=50)
        if face:
            d.polygon([(cx-rx*.5,cy-ry*.25),(cx-rx*.2,cy-ry*.6),(cx-rx*.1,cy-ry*.15)],fill=15)
            d.polygon([(cx+rx*.5,cy-ry*.25),(cx+rx*.2,cy-ry*.6),(cx+rx*.1,cy-ry*.15)],fill=15)
            d.polygon([(cx-6,cy),(cx,cy-12),(cx+6,cy)],fill=15)
            pts=[(cx-rx*.55+i*rx*1.1/8, cy+ry*.35+(10 if i%2 else -2)) for i in range(9)]
            d.polygon(pts+[(cx+rx*.5,cy+ry*.62),(cx-rx*.5,cy+ry*.62)],fill=15)
    pk(400,150,120,78); pk(220,175,55,36,False); pk(590,178,60,40,False); pk(130,190,36,24,False)
    for bx,by,sc in [(130,50,1.2),(250,90,.8),(500,40,1),(700,150,.9),(60,110,.7)]:
        d.polygon([(bx,by),(bx-28*sc,by-12*sc),(bx-40*sc,by+4*sc),(bx-22*sc,by+2*sc),(bx-12*sc,by+12*sc),(bx,by+4*sc),(bx+12*sc,by+12*sc),(bx+22*sc,by+2*sc),(bx+40*sc,by+4*sc),(bx+28*sc,by-12*sc)],fill=10)
    return im.filter(ImageFilter.GaussianBlur(1.2))
def scene(W=800,H=240):
    return pumpkin(W,H)
def scene_school(W=800,H=240):
    im=Image.new('L',(W,H),245); d=ImageDraw.Draw(im)
    # sky gradient hatch tone
    for y in range(H): d.line([(0,y),(W,y)],fill=int(236-y*0.12))
    # ground
    d.rectangle([0,198,W,H],fill=150)
    for y in range(198,H): d.line([(0,y),(W,y)],fill=int(185-(y-198)*2.2))
    # path
    d.polygon([(370,H),(430,H),(418,198),(382,198)],fill=215)
    # building body
    d.rectangle([200,110,600,200],fill=190)
    d.rectangle([200,110,600,122],fill=120)           # cornice shadow
    d.rectangle([560,122,600,200],fill=150)           # side shade
    # wings columns
    for x in (330,355,445,470): d.rectangle([x,128,x+10,200],fill=225)
    d.polygon([(320,128),(400,82),(480,128)],fill=205) # pediment
    d.polygon([(320,128),(400,82),(480,128),(470,128),(400,92),(330,128)],fill=110)
    # roof
    d.polygon([(185,112),(300,62),(500,62),(615,112)],fill=75)
    d.polygon([(300,62),(500,62),(520,72),(280,72)],fill=100)
    # tower
    d.rectangle([370,6,430,70],fill=200); d.rectangle([420,6,430,70],fill=140)
    d.polygon([(362,10),(400,-14),(438,10)],fill=70)
    d.ellipse([385,24,415,54],fill=245); d.ellipse([385,24,415,54],outline=40,width=3)
    d.line([(400,39),(400,28)],fill=30,width=2); d.line([(400,39),(408,39)],fill=30,width=2)
    # windows
    for x0 in (225,265,520,560):
        d.rectangle([x0,138,x0+26,178],fill=60)
        d.line([(x0+13,138),(x0+13,178)],fill=200,width=2); d.line([(x0,158),(x0+26,158)],fill=200,width=2)
    d.rectangle([382,150,418,200],fill=50)  # door
    d.polygon([(380,150),(400,138),(420,150)],fill=50)
    # steps
    for i in range(3): d.rectangle([372-i*6,200+i*0,428+i*6,200],fill=210)
    # tree left
    d.rectangle([108,130,122,205],fill=70)
    for cx,cy,r,v in [(115,110,48,95),(88,130,34,80),(142,128,36,70),(115,85,32,110)]:
        d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=v)
    d.ellipse([125,95,160,130],fill=60)
    # tree right
    d.rectangle([688,140,700,205],fill=70)
    for cx,cy,r,v in [(694,118,42,100),(670,138,30,80),(722,136,32,70),(694,92,28,115)]:
        d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=v)
    # flagpole + flag
    d.line([(640,60),(640,200)],fill=40,width=3); d.polygon([(642,62),(690,70),(642,86)],fill=70)
    # sign
    d.rectangle([252,196,292,214],fill=235); d.rectangle([252,196,292,214],outline=40,width=2)
    # kids silhouettes
    for x in (300,320,486,510):
        d.ellipse([x-5,172,x+5,182],fill=40); d.polygon([(x-7,184),(x+7,184),(x+9,208),(x-9,208)],fill=55)
    # cloud
    for cx,cy,r in [(540,36,20),(565,30,26),(595,38,18)]: d.ellipse([cx-r,cy-r*.7,cx+r,cy+r*.7],fill=252)
    return im.filter(ImageFilter.GaussianBlur(1.2))
def svg(seed=7):
    random.seed(seed)
    im=scene(); W,H=im.size; a=np.array(im).astype(float)
    # edges via gradient for contour
    gy,gx=np.gradient(a)
    out=[]
    # stipple: poisson-ish via jittered grid, density by darkness
    step=4.2
    y=2.0
    while y<H:
        x=2.0+(random.random()*step)
        while x<W:
            xi,yi=int(min(W-1,x)),int(min(H-1,y))
            v=a[yi,xi]; dark=(255-v)/255
            if random.random()<dark**1.15*1.05:
                r=0.45+dark*1.05
                out.append(f'<circle cx="{x/2:.1f}" cy="{y/2:.1f}" r="{r/2*1.15:.2f}"/>')
            x+=step*(0.8+0.4*random.random())
        y+=step*0.82
    # hatch lines in dark areas (engraving feel)
    hatch=[]
    for yy in range(0,H,5):
        run=None
        for xx in range(0,W+1):
            dk=(255-a[min(yy,H-1),min(xx,W-1)])/255 if xx<W else 0
            if dk>0.62 and run is None: run=xx
            if (dk<=0.62) and run is not None:
                if xx-run>6: hatch.append(f'<line x1="{run/2:.1f}" y1="{yy/2:.1f}" x2="{xx/2:.1f}" y2="{yy/2:.1f}"/>')
                run=None
    # outlines at strong edges
    mag=np.hypot(gx,gy)
    for yy in range(1,H-1,2):
        for xx in range(1,W-1,2):
            if mag[yy,xx]>26: out.append(f'<circle cx="{xx/2:.1f}" cy="{yy/2:.1f}" r="0.5"/>')
    return (f'<svg viewBox="0 0 400 120" width="100%" xmlns="http://www.w3.org/2000/svg"><rect width="400" height="120" fill="#f6f1e1"/>'
            f'<g fill="#1a1713">{"".join(out)}</g><g stroke="#1a1713" stroke-width="0.45">{"".join(hatch)}</g>'
            f'<rect x="1" y="1" width="398" height="118" fill="none" stroke="#1a1713" stroke-width="0.6"/></svg>')
if __name__=='__main__':
    s=svg(); open('hed.svg','w').write(s); print(len(s))
