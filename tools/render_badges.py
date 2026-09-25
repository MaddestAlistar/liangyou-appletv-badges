"""Render versioned, font-independent badges without changing historical assets."""
from __future__ import annotations
import argparse, concurrent.futures, copy, io, json, os, re, subprocess
from pathlib import Path
from lxml import etree as ET
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
import badge_rules as rules
import badge_icons

ROOT=rules.ROOT
ASSETS=ROOT/'assets'/rules.VERSION
NS='http://www.w3.org/2000/svg'
PALETTE={'gold':('#F4C65D','#FFE58A','#E8A819'),'purple':('#C28BFF','#D0ACFF','#8748DD'),'blue':('#7ACDFA','#9CDEFF','#268BE5'),'orange':('#FFAA58','#FFD18B','#F37B27')}
FONT=None;FONTFILE=None;GLYPHS=None;CMAP=None;UPM=1000

def set_font(path=None):
    global FONT,FONTFILE,GLYPHS,CMAP,UPM
    candidates=[path,os.environ.get('LIANGYOU_FONT'),'/root/.local/share/fonts/liangyou-preview/NotoSansCJKsc-Bold.otf','/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc']
    FONTFILE=next((Path(x) for x in candidates if x and Path(x).is_file()),None)
    if not FONTFILE:raise RuntimeError('Provide --font with Noto Sans CJK SC Bold OTF/TTC.')
    FONT=TTFont(FONTFILE,fontNumber=0);GLYPHS=FONT.getGlyphSet();CMAP=FONT.getBestCmap();UPM=FONT['head'].unitsPerEm
    badge_icons.pathtext=pathtext

def text_width(text,size):return sum(GLYPHS[CMAP.get(ord(c),'.notdef')].width for c in text)*size/UPM

def pathtext(text,x,y,size,color,center=False,maxwidth=None,spacing=0):
    width=text_width(text,size)+max(0,len(text)-1)*spacing
    if maxwidth and width>maxwidth:size*=maxwidth/width;spacing*=maxwidth/width;width=maxwidth
    if center:x-=width/2
    parent=ET.Element('{'+NS+'}g',{'aria-label':text,'fill':color,'transform':f'translate({x:.4f} {y:.4f}) scale({size/UPM:.7f} {-size/UPM:.7f})'})
    pos=0
    for c in text:
        glyph=GLYPHS[CMAP.get(ord(c),'.notdef')];pen=SVGPathPen(GLYPHS);glyph.draw(pen)
        if pen.getCommands():ET.SubElement(parent,'{'+NS+'}path',{'d':pen.getCommands(),'transform':f'translate({pos:.4f} 0)'})
        pos+=glyph.width+spacing*UPM/size
    return ET.tostring(parent,encoding='unicode')

def el(s):return ET.fromstring(s.encode())

def outline_text(root,width):
    for node in list(root.iter('{'+NS+'}text')):
        text=''.join(node.itertext());x=float(node.get('x','0'));y=float(node.get('y','0'));size=float(node.get('font-size','20'))
        center=node.get('text-anchor')=='middle'
        # Keep original coordinates, while ensuring the intended font fits inside the frame.
        maxw=width-x-14 if x>85 and not center else None
        new=el(pathtext(text,x,y,size,node.get('fill','#FFFFFF'),center,maxw,float(node.get('letter-spacing','0'))))
        if node.get('transform'):new.set('transform',node.get('transform')+' '+new.get('transform'))
        node.getparent().replace(node,new)

def brighten_dolby(root,version,c):
    # Replace dark Double-D interiors with bright native paths, not a dark cutout.
    groups=root.findall('{'+NS+'}g')
    if version=='all':
        target=next((g for g in groups if g.get('filter')=='url(#glow)'),None)
        if target is not None:
            keep=[n for n in target if ET.QName(n).localname=='circle']
            for n in list(target):target.remove(n)
            for n in keep:target.append(n)
            glyph=el(f'<g xmlns="{NS}" transform="translate(41 27) scale(.94)">{badge_icons.icon_paths("dolby",c,"dolby")}</g>')
            target.append(glyph)
    else:
        target=next((g for g in groups if g.get('transform')=='translate(-14 0)'),None)
        if target is not None:
            for n in target.iter():
                if n.get('fill') and n.get('fill')!='none':n.set('fill',c)
                if n.get('stroke'):n.set('stroke',c)

def new_svg(b,version):
    c,light,strong=PALETTE[b['color']]
    if version=='epx':
        defs=f'<defs><linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c}" stop-opacity=".95"/><stop offset=".52" stop-color="#FFFFFF" stop-opacity=".48"/><stop offset="1" stop-color="{c}" stop-opacity=".95"/></linearGradient></defs>'
        base=f'<rect x="3" y="3" width="314" height="90" rx="19" fill="none" stroke="url(#edge)" stroke-width="2.5"/><rect x="7" y="7" width="306" height="82" rx="16" fill="none" stroke="#FFFFFF" stroke-opacity=".14" stroke-width="1"/><circle cx="20" cy="18" r="9.5" fill="none" stroke="{c}" stroke-width="1.6"/>'
        base+=pathtext('良',20,22.5,12.5,c,True)
        base+=f'<circle cx="61" cy="49" r="26" fill="none" stroke="{c}" stroke-width="2.1" stroke-opacity=".75"/><g transform="translate(37 25) scale(.8)">{badge_icons.icon_paths(b["icon"],light,b["slug"])}</g><path d="M106 20v56" stroke="{c}" stroke-opacity=".45" stroke-width="1.5"/>'
        base+=pathtext(b['title'],114,47,33,'#FFFFFF',maxwidth=191)
        base+=pathtext(b['subtitle'],114,73,21,c,maxwidth=190)
        return el(f'<svg xmlns="{NS}" width="320" height="96" viewBox="0 0 320 96">{defs}{base}</svg>')
    source=ET.parse(str(ROOT/'badges-premium-svg/web-dl.svg')).getroot()
    # The premium frame and gradient structure are taken directly from the original set.
    for n in list(source):
        if ET.QName(n).localname=='g' or (ET.QName(n).localname=='path' and n.get('d','').startswith('M112')) or (ET.QName(n).localname=='text' and n.text!='良'):
            source.remove(n)
    for n in source.iter():
        for a in ['fill','stroke','stop-color']:
            if n.get(a)=='#8BD9FF':n.set(a,light)
            if n.get(a)=='#087DFF':n.set(a,strong)
    body=f'<g xmlns="{NS}" filter="url(#glow)"><circle cx="69" cy="55" r="35" fill="#05070A" stroke="{strong}" stroke-width="2.2"/><circle cx="69" cy="55" r="31" fill="url(#iconFill)" opacity=".34"/><circle cx="69" cy="55" r="32" fill="none" stroke="{light}" stroke-opacity=".58" stroke-width="2"/><g transform="translate(41 27) scale(.94)">{badge_icons.icon_paths(b["icon"],light,b["slug"])}</g></g>'
    source.append(el(body));source.append(el(f'<path xmlns="{NS}" d="M112 21v66" stroke="{light}" stroke-opacity=".55" stroke-width="1.8"/>'))
    source.append(el(pathtext(b['title'],124,55,36,'#FFFFFF',maxwidth=219)))
    source.append(el(pathtext(b['subtitle'],124,82,22,light,maxwidth=218)))
    return source

def make_svg(b,version):
    legacy=ROOT/('Badge-LiangYou-Ver.EPX-v6' if version=='epx' else 'badges-premium-svg')/(b['slug']+'.svg')
    c,light,strong=PALETTE[b['color']]
    if b.get('original') and legacy.exists():
        root=ET.parse(str(legacy)).getroot()
        edge=root.find('.//{'+NS+'}linearGradient[@id="edge"]')
        old=[n.get('stop-color') for n in edge if n.get('stop-color')!='#FFFFFF']
        mapping={old[0]:c if version=='epx' else light}
        if version=='all' and len(set(old))>1:mapping[old[1]]=strong
        for n in root.iter():
            for a in ['fill','stroke','stop-color']:
                if n.get(a) in mapping:n.set(a,mapping[n.get(a)])
        if b['slug'] in ['dolby-vision','atmos']:brighten_dolby(root,version,light)
        if b['slug']=='dtshd-core':
            for n in root.iter('{'+NS+'}text'):
                if n.text=='HIGH RES AUDIO':n.text='HD AUDIO'
        if b['slug']=='dtshd' and version=='all':
            for n in list(root.findall('{'+NS+'}text')):
                if n.text!='良':root.remove(n)
            root.append(el(pathtext(b['title'],124,55,36,'#FFFFFF',maxwidth=219)))
            root.append(el(pathtext(b['subtitle'],124,82,22,light,maxwidth=218)))
    else:root=new_svg(b,version)
    width=320 if version=='epx' else 360
    outline_text(root,width)
    # No font substitution, external resources or variable visible canvas extents.
    for n in list(root):
        if ET.QName(n).localname=='rect' and n.get('x')=='0' and n.get('y')=='0':root.remove(n)
    if version=='all':
        wrapper=ET.Element('{'+NS+'}g',{'transform':'scale(0.8888888889)'})
        for n in list(root):
            if ET.QName(n).localname!='defs':root.remove(n);wrapper.append(n)
        root.append(wrapper)
    for k,v in dict(width='320',height='96',viewBox='0 0 320 96',preserveAspectRatio='xMidYMid meet',overflow='hidden').items():root.set(k,v)
    root.insert(0,el(f'<rect xmlns="{NS}" x="0" y="0" width="320" height="96" fill="#000000" fill-opacity="0.004"/>'))
    return ET.tostring(root,encoding='unicode')+'\n'

def render_png(job):
    svg,png=job;png.parent.mkdir(parents=True,exist_ok=True)
    if png.exists() and png.stat().st_mtime>=svg.stat().st_mtime:
        try:
            with Image.open(png) as im:im.load()
            return
        except OSError:pass
    proc=subprocess.run(['inkscape','--batch-process',f'--app-id-tag=ly8-{svg.stem}-{svg.parent.parent.name}',str(svg),'--export-type=png','--export-width=960','--export-height=288','--export-filename=-'],capture_output=True)
    if proc.returncode:raise RuntimeError(proc.stderr.decode(errors='replace'))
    with Image.open(io.BytesIO(proc.stdout)) as im:
        im.load()
        if im.size!=(960,288):raise AssertionError((png,im.size))
    temp=png.with_suffix('.stage');temp.write_bytes(proc.stdout);os.replace(temp,png)

def render_all():
    jobs=[]
    for version in ['epx','all']:
        items=rules.catalogue(version)
        if version=='epx':items+=[dict(slug='size-test',title='SIZE TEST',subtitle='320 × 96',category='diagnostic',color='orange',icon='screen')]
        for b in items:
            p=ASSETS/version/'svg'/(b['slug']+'.svg');p.parent.mkdir(parents=True,exist_ok=True)
            text=make_svg(b,version)
            if not p.exists() or p.read_text()!=text:p.write_text(text)
            jobs.append((p,ASSETS/version/'png'/(b['slug']+'.png')))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(render_png,jobs))

SECTIONS=[('combo','条件组合'),('resolution','分辨率'),('source','片源'),('video','画面与色彩'),('codec','视频编码'),('audio','音频格式'),('channels','声道'),('platform','平台来源'),('edition','版本标识'),('language','音轨语言')]

def preview(version,combos_only=False):
    data=rules.catalogue(version);data=[b for b in data if not combos_only or b['category']=='combo']
    # Profile combinations are in the full catalogue; present generic forms in the comparison sheet.
    if combos_only:data=[b for b in data if not re.search(r'-p[578]$',b['slug'])]
    groups=[(name,[b for b in data if b['category']==key]) for key,name in SECTIONS]
    groups=[g for g in groups if g[1]]
    w=1598;pad=66;bw=350;bh=105;gap=22;step=126
    h=250+sum(62+((len(bs)+3)//4)*step+24 for _,bs in groups)+105
    im=Image.new('RGB',(w,h),'#0A101B');d=ImageDraw.Draw(im)
    font=lambda n:ImageFont.truetype(str(FONTFILE),n)
    d.text((pad,30),'LIANGYOU  /  MEDIA BADGES',font=font(21),fill='#8DCFFA')
    title='良友徽章 · '+('EplayerX' if version=='epx' else '复杂版')+(' · 组合示例' if combos_only else ' · V8')
    d.text((pad,69),title,font=font(47),fill='#F5F7FC')
    desc='同文本组合优先 · 对应单项互斥 · 明亮杜比图标' if combos_only else f'{len(data)} 枚徽章 · 统一画布 · 矢量文字 · 条件组合'
    d.text((pad,144),desc,font=font(23),fill='#A5B2C5')
    for x,c,label in [(pad,'#F4C65D','金色：重点 / 杜比'),(pad+380,'#C28AFF','紫色：次级'),(pad+685,'#7ACDFA','蓝色：常规'),(pad+990,'#FFAA58','橘色：组合 / 特殊')]:
        d.ellipse((x,199,x+12,211),fill=c);d.text((x+23,187),label,font=font(21),fill='#A5B2C5')
    y=260
    for index,(name,items) in enumerate(groups,1):
        d.text((pad,y),f'{index:02d}  {name}',font=font(27),fill='#DFE8F5');d.line((pad+320,y+23,w-pad,y+23),fill='#2B3545');y+=62
        for i,b in enumerate(items):
            img=Image.open(ASSETS/version/'png'/(b['slug']+'.png')).convert('RGBA').resize((bw,bh),Image.Resampling.LANCZOS)
            im.paste(img,(pad+(i%4)*(bw+gap),y+(i//4)*step),img)
        y+=((len(items)+3)//4)*step+24
    d.line((pad,h-85,w-pad,h-85),fill='#2B3545');d.text((pad,h-66),'良哥看未来 · 2026.09.24',font=font(20),fill='#92A4BC')
    d.text((w-545,h-66),'配色为展示分级，实际显示取决于匹配输入',font=font(17),fill='#92A4BC')
    out=ROOT/'previews'/('Combos-v8.png' if combos_only else ('EPX-v8.png' if version=='epx' else 'ALL-v8.png'))
    out.parent.mkdir(exist_ok=True);im.save(out,optimize=True)
    return out

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--font');parser.add_argument('--previews-only',action='store_true');args=parser.parse_args()
    set_font(args.font)
    if not args.previews_only:render_all()
    print(json.dumps({'previews':[str(preview('epx')),str(preview('all')),str(preview('all',True))]},ensure_ascii=False))
