"""LiangYou v8. Rules describe one media source's input text, not playback capability.

Java Pattern and ICU syntax. No custom JSON fields with unverified client support.
Whole-input anchors and [\\s\\S] make exclusions work across line breaks.
"""
from __future__ import annotations
import copy
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSION='2026-09-24-v8'
BASE=f'https://raw.githubusercontent.com/MaddestAlistar/liangyou-appletv-badges/main/assets/{VERSION}'
SEP=r'[\s._-]*'

def tok(s):
    return rf'(?:^|[^A-Za-z0-9])(?:{s})(?![A-Za-z0-9])'

def atok(s):
    return rf'(?:^|[^A-Za-z0-9])(?:{s})(?=$|[^A-Za-z0-9]|[12567][.]\d)'

def anyof(*s):
    return '(?:'+'|'.join(s)+')'

def condition(*required, exclude=()):
    return r'\A'+''.join(r'(?=[\s\S]*(?:'+p+'))' for p in required)+''.join(r'(?![\s\S]*(?:'+p+'))' for p in exclude)+r'[\s\S]+'

def whole(*required, exclude=()):
    return '(?i)'+condition(*required,exclude=exclude)

P={}
P['1080p']=tok(r'1080[pi]?|fhd|full[\s._-]*hd|1920\s*[x×*]\s*(?:1080|[89]\d{2})')
P['720p']=tok(r'720[pi]?|1280\s*[x×*]\s*720')
P['576p']=tok(r'576[pi]?|720\s*[x×*]\s*576')
P['480p']=tok(r'480[pi]?|(?:720|640)\s*[x×*]\s*480')
# UHD alone is a fallback, not proof that a 1080p encode is 4K.
P['4k']=anyof(tok(r'2160[pi]?|4k|(?:3840|4096)\s*[x×*]\s*\d{3,4}'),r'超高清',condition(tok(r'uhd|ultra[\s._-]*hd'),exclude=(anyof(P['1080p'],P['720p'],P['576p'],P['480p']),)))
P['remux']=tok(r'(?:(?:bd|uhd|blu[\s._-]*ray)[\s._-]*)?remux')
P['bluray']=tok(r'blu[\s._-]*ray|bluray|bdrip|brrip|bdmv|bd25|bd50|bd66|bd100|bdmux')
P['web-dl']=tok(r'web[\s._-]*(?:dl|download)')
P['webrip']=tok(r'web[\s._-]*rip')
P['hdtv']=tok(r'hdtv')
P['dvdrip']=tok(r'dvd[\s._-]*rip')
P['dolby-vision']=anyof(tok(r'dolby[\s._-]*vision|dovi|dv(?:[578])?|dvhe(?:\.\d+(?:\.\d+)?)?|dvh1(?:\.\d+(?:\.\d+)?)?'),r'杜比视界',r'\u2063')
for p in [5,7,8]:
    P[f'dv-p{p}']=anyof(tok(rf'(?:dvhe|dvh1)\.0?{p}(?:\.\d+)?'),tok(rf'(?:dovi|dv|dolby[\s._-]*vision)[\s._-]*(?:(?:p|profile)[\s._:-]*)?0?{p}(?:\.\d+)?'),tok(rf'(?:dv[\s._-]*profile|dovi[\s._-]*profile)[\s._:=]*0?{p}'),rf'杜比视界[\s._-]*(?:P|Profile)?0?{p}(?!\d)')
P['atmos']=anyof(atok(r'dolby[\s._-]*atmos|atmos|joc'),r'杜比全景声|全景声')
P['truehd']=atok(r'true[\s._-]*hd|dolby[\s._-]*truehd|mlp[\s._-]*fba')
P['ddplus']=anyof(atok(r'dolby[\s._-]*digital[\s._-]*plus|e[\s._-]*ac[\s._-]*3'),r'(?:^|[^A-Za-z0-9])(?:ddp|dd\+)(?=$|[^A-Za-z0-9]|[12567][.]\d)')
P['dd']=anyof(atok(r'ac[\s._-]*3'),r'(?:^|[^A-Za-z0-9])(?:dolby[\s._-]*digital|dd)(?![A-Za-z]|[\s._-]*(?:\+|plus))(?=$|[^A-Za-z0-9]|[12567][.]\d)')
P['dtshd']=atok(r'dts[\s._-]*hd[\s._-]*(?:ma|master(?:[\s._-]*audio)?)|dts[\s._-]*ma|dts[\s._-]*xll')
P['dtshd-core']=atok(r'dts[\s._-]*hd(?:[\s._-]*hra)?')
P['dtsx']=atok(r'dts[:\s._-]*x')
P['dts']=atok(r'dts')
P['hdr10plus']=anyof(r'(?:^|[^A-Za-z0-9])hdr[\s._-]*10[\s._-]*(?:\+|plus|p)(?![A-Za-z0-9])',r'\u2064')
P['hdr10']=tok(r'hdr[\s._-]*10')
P['hlg']=tok(r'hlg|hybrid[\s._-]*log[\s._-]*gamma')
P['hdr']=tok(r'hdr|high[\s._-]*dynamic[\s._-]*range|smpte[\s._-]*2084')
P['sdr']=tok(r'sdr|standard[\s._-]*dynamic[\s._-]*range')
P['imax-enhanced']=tok(r'imax[\s._-]*enhanced')
P['imax']=tok(r'imax')
P['hevc']=tok(r'hevc|h[\s._-]*265|x265|hvc1|hev1|mpeg[\s._-]*h[\s._-]*part[\s._-]*2')
P['avc']=tok(r'avc|h[\s._-]*264|x264|avc1|mpeg[\s._-]*4[\s._-]*(?:avc|part[\s._-]*10)')
P['av1']=tok(r'av1|av01')
P['vp9']=tok(r'vp9|vp09')
P['mpeg2']=tok(r'mpeg[\s._-]*2(?:video)?')
P['vc1']=tok(r'vc[\s._-]*1|wmv3')
for slug in ['xvid','divx','flac','opus','mp3']:
    P[slug]=atok(slug) if slug in ['flac','opus','mp3'] else tok(slug)
P['aac']=atok(r'aac(?:[\s._-]*(?:latm|lc|he))?|mp4a')
P['pcm']=atok(r'l?pcm(?:[_-](?:s|u|f)\d+(?:le|be)?)?')
for b in [8,10]:
    P[f'{b}bit']=anyof(tok(rf'{b}[\s._-]*bits?'),tok(rf'yuv\d+p{b}(?:le|be)?|p0{b}(?:le|be)'),rf'(?:video[\s._-]*(?:bit[\s._-]*depth)|视频位深)[\s:="\']*{b}(?!\d)')
P['3d']=tok(r'3d|hsbs|htab|half[\s._-]*sbs|full[\s._-]*sbs')
for f in [50,60,120]:
    P[f'{f}fps']=anyof(tok(rf'{f}(?:\.0+)?[\s._-]*fps'),rf'(?:frame[\s._-]*rate|帧率)[\s:="\']*{f}(?:\.0+)?(?![\d.])')

AUDIO=anyof(P['truehd'],P['atmos'],P['ddplus'],P['dd'],P['dtshd'],P['dtshd-core'],P['dtsx'],P['dts'],P['aac'],P['flac'],P['pcm'],P['opus'],P['mp3'])
codec_prefix=r'(?:true[\s._-]*hd|atmos|ddp|dd\+|e[\s._-]*ac[\s._-]*3|ac[\s._-]*3|dts(?:[\s._-]*hd(?:[\s._-]*ma)?)?|aac|flac|opus|l?pcm)'
for slug,num,alias in [('10','1.0','mono'),('20','2.0','stereo'),('51','5.1',''),('61','6.1',''),('71','7.1','')]:
    n=num.replace('.',r'[ ._-]?')
    explicit=anyof(rf'(?:^|[^A-Za-z0-9]){codec_prefix}[\s._:-]*{n}(?!\d)',rf'(?:audio[\s._-]*channels?|channel[\s._-]*layout|音频声道|声道)[\s:="\']*{n}(?!\d)',rf'(?:^|[^A-Za-z0-9]){n}[\s._-]*(?:ch(?:annels?)?|声道)(?![A-Za-z0-9])',rf'\A\s*{num.replace(".",r"\.")}\s*\Z')
    if alias:explicit=anyof(explicit,rf'(?:audio|音轨|声道)[\s:._-]*{alias}(?![A-Za-z])',rf'(?:^|[^A-Za-z0-9]){alias}[\s._-]*(?:audio|声道)(?![A-Za-z])',rf'\A\s*{alias}\s*\Z')
    if slug in ['51','61','71']:
        bare=rf'(?<![A-Za-z0-9])(?<!level[ .:_-])(?<!level:[ ])(?<!profile[ .:_-])(?<!profile:[ ]){num.replace(".",r"\.")}(?![\d.]\d)'
        explicit=anyof(explicit,bare)
    P[slug]=explicit

platforms={'netflix':r'netflix|nf','prime-video':r'prime[\s._-]*video|amzn','apple-tv':r'apple[\s._-]*tv\+|atvp','disney-plus':r'disney\+|dsnp','max':r'hbo[\s._-]*max|hmax','hulu':r'hulu','peacock':r'peacock|pcok','paramount-plus':r'paramount\+|pmtp','crunchyroll':r'crunchyroll'}
WEB=anyof(P['web-dl'],P['webrip'])
for slug,rx in platforms.items():
    # Explicit platform field also works without a WEB tag; bare MAX/CR are deliberately excluded.
    P[slug]=anyof(rf'(?:platform|service|来源|平台)[\s:="\']*(?:{rx})(?![A-Za-z0-9])',condition(WEB,tok(rx)))
editions={'directors-cut':r'director[\s._-]*[\x27’]?s?[\s._-]*cut','extended':r'extended(?:[\s._-]*cut)?','remastered':r'remastered','open-matte':r'open[\s._-]*matte','repack':r'repack(?:\d+)?','proper':r'proper','criterion':r'criterion','hybrid':r'hybrid(?![\s._-]*log[\s._-]*gamma)','black-white':r'black[\s._-]*(?:and|&)[\s._-]*white|b&w','theatrical':r'theatrical(?:[\s._-]*cut)?'}
for slug,rx in editions.items():P[slug]=tok(rx)
for slug,rx,ch in [('chinese',r'chi|zho|zh(?:[-_]cn)?|chinese','中文|国语|普通话'),('english',r'eng|en|english','英语|英文'),('japanese',r'jpn|ja|japanese','日语|日文'),('korean',r'kor|ko|korean','韩语|韩文')]:
    P[slug]=anyof(rf'(?:audio(?:[\s._-]*language)?|音轨|配音)[\s:="\']*(?:{rx}|{ch})(?![A-Za-z])',rf'(?:{ch})(?:音轨|配音)',rf'(?:{rx})[\s._-]*audio(?![A-Za-z])')

# Slug, required media facts, exclusions, label, subtitle.
COMBOS=[
 ('combo-dv-atmos-truehd',('dolby-vision','atmos','truehd'),(), 'DV + ATMOS','TRUEHD'),
 ('combo-dv-atmos-ddplus',('dolby-vision','atmos','ddplus'),('truehd',),'DV + ATMOS','DD+ / E-AC-3'),
 ('combo-dv-atmos',('dolby-vision','atmos'),('truehd','ddplus'),'DV + ATMOS','杜比视界 · 全景声'),
 ('combo-dv-truehd',('dolby-vision','truehd'),('atmos',),'DV + TRUEHD','杜比视界 · 无损音频'),
 ('combo-atmos-truehd',('atmos','truehd'),('dolby-vision',),'ATMOS + TRUEHD','杜比全景声 · TRUEHD'),
 ('combo-atmos-ddplus',('atmos','ddplus'),('dolby-vision','truehd'),'ATMOS + DD+','杜比全景声 · E-AC-3'),
 ('combo-dtsx-dtshd',('dtsx','dtshd'),(),'DTS:X + HD MA','沉浸音频 · MASTER AUDIO'),
]

OLD=[
 ('4k','良友4K','ULTRA HD','resolution','tv'),('1080p','1080P','FULL HD','resolution','tv'),('720p','720P','HD','resolution','tv'),
 ('remux','REMUX','MASTER','source','film'),('dolby-vision','DOLBY VISION','杜比视界','video','dolby'),('atmos','DOLBY ATMOS','杜比全景声','audio','dolby'),
 ('truehd','TRUEHD','LOSSLESS AUDIO','audio','wave'),('dtshd','DTS-HD','MASTER AUDIO','audio','wave'),('dtshd-core','DTS-HD','HD AUDIO','audio','wave'),('dtsx','DTS:X','IMMERSIVE AUDIO','audio','wave'),('dts','DTS','CORE AUDIO','audio','wave'),
 ('hdr10plus','HDR10+','DYNAMIC HDR','video','sun'),('hdr10','HDR10','STATIC HDR','video','sun'),('hlg','HLG','HYBRID LOG GAMMA','video','sun'),
 ('51','5.1','SURROUND AUDIO','channels','speaker'),('71','7.1','SURROUND AUDIO','channels','speaker'),
 ('hevc','HEVC','VIDEO CODEC','codec','chip'),('av1','AV1','VIDEO CODEC','codec','chip'),('avc','AVC','VIDEO CODEC','codec','chip'),('vp9','VP9','VIDEO CODEC','codec','chip'),
 ('bluray','BLU-RAY','DISC SOURCE','source','disc'),('web-dl','WEB-DL','WEB SOURCE','source','web'),('flac','FLAC','LOSSLESS AUDIO','audio','wave'),('aac','AAC','AUDIO CODEC','audio','wave')]

GOLD={'4k','remux','uhd-bluray','dolby-vision','atmos','truehd','dd','ddplus','dv-p5','dv-p7','dv-p8','hdr10plus','imax-enhanced','10bit','av1','dtsx','dtshd','flac','pcm','71','120fps'}
PURPLE={'1080p','bluray','web-dl','hdr10','hlg','imax','hevc','dtshd-core','opus','51','61','60fps'}

def metadata():
    by={s:dict(slug=s,title=t,subtitle=sub,category=cat,icon=ic,epx=True,original=True) for s,t,sub,cat,ic in OLD}
    for b in json.loads((ROOT/'tools/new_badge_catalogue.json').read_text()):
        if b['slug'] not in by:by[b['slug']]=copy.deepcopy(b)
    for s,b in by.items():
        b['color']='gold' if s in GOLD or b['category']=='edition' else 'purple' if s in PURPLE else 'orange' if s=='3d' else 'blue'
    return by

def combo_specs(version):
    specs=[]
    for slug,req,exc,title,sub in COMBOS:
        if version=='all' and 'dolby-vision' in req:
            for profile in [5,7,8]:
                p=f'dv-p{profile}'
                other=tuple(f'dv-p{x}' for x in [5,7,8] if x!=profile)
                specs.append(dict(slug=f'{slug}-p{profile}',required=req+(p,),excluded=exc+other,title=title.replace('DV',f'DV P{profile}',1),subtitle=sub,category='combo',icon='dolby',color='orange',epx=False))
            # Ambiguous multiple profile tags fall back to generic DV, not an invented profile.
            prof_unambiguous=anyof(*(condition(P[f'dv-p{x}'],exclude=tuple(P[f'dv-p{y}'] for y in [5,7,8] if y!=x)) for x in [5,7,8]))
            specs.append(dict(slug=slug,required=req,excluded=exc,extra_excluded=(prof_unambiguous,),title=title,subtitle=sub,category='combo',icon='dolby',color='orange',epx=True))
        else:
            specs.append(dict(slug=slug,required=req,excluded=exc,title=title,subtitle=sub,category='combo',icon='wave' if 'dtsx' in slug else 'dolby',color='orange',epx=True))
    return specs

def single_rule(slug,version,combos=True):
    req=[P[slug]]; exc=[]
    res=['4k','1080p','720p','576p','480p']
    if slug in res:exc.extend(P[s] for s in res[:res.index(slug)])
    if slug=='uhd-bluray':req=[P['4k'],P['bluray']];exc=[P['remux']]
    if slug=='bluray':exc=[P['remux'],P['4k']]
    if slug in ['web-dl','webrip','hdtv','dvdrip']:
        exc.extend([P['remux'],P['bluray']])
        if slug=='web-dl':exc.append(P['webrip'])
        if slug in ['hdtv','dvdrip']:exc.append(WEB)
    if slug=='hdr10':exc.append(P['hdr10plus'])
    if slug=='hdr':exc.extend(P[s] for s in ['hdr10plus','hdr10','hlg','dolby-vision'])
    if slug=='sdr':exc.extend(P[s] for s in ['hdr10plus','hdr10','hlg','dolby-vision','hdr'])
    if slug=='imax':exc.append(P['imax-enhanced'])
    if slug=='8bit':exc.append(P['10bit'])
    if slug=='dtshd-core':exc.append(P['dtshd'])
    if slug=='dts':exc.extend(P[s] for s in ['dtshd','dtshd-core','dtsx'])
    # Never label EAC3 as Atmos. DD doesn't match DD+ in the first place.
    if slug=='dd':exc.append(P['ddplus'])
    if slug in ['10','20','51','61','71']:
        order=['71','61','51','20','10'];exc.extend(P[s] for s in order[:order.index(slug)])
    if slug in ['50fps','60fps']:exc.extend(P[s] for s in (['60fps','120fps'] if slug=='50fps' else ['120fps']))
    if slug.startswith('dv-p'):
        exc.extend(P[f'dv-p{x}'] for x in [5,7,8] if f'dv-p{x}'!=slug)
    if slug=='dolby-vision' and version=='all':
        for x in [5,7,8]:
            exc.append(condition(P[f'dv-p{x}'],exclude=tuple(P[f'dv-p{y}'] for y in [5,7,8] if y!=x)))
    if combos:
        if slug=='dolby-vision' or slug.startswith('dv-p'):exc.append(anyof(P['atmos'],P['truehd']))
        if slug=='truehd':exc.append(anyof(P['dolby-vision'],P['atmos']))
        if slug=='atmos':exc.append(anyof(P['dolby-vision'],P['truehd'],P['ddplus']))
        if slug=='ddplus':exc.append(condition(P['atmos'],exclude=(P['truehd'],)))
        if slug=='dtsx':exc.append(P['dtshd'])
        if slug=='dtshd':exc.append(P['dtsx'])
    return whole(*req,exclude=exc)

def catalogue(version,combos=True):
    data=metadata()
    if version=='epx':data={s:b for s,b in data.items() if b['epx']}
    # Defines priority in clients that preserve array order. Regex handles overlap separately.
    first=['4k','1080p','720p','576p','480p','remux','uhd-bluray']
    items=[data.pop(s) for s in first if s in data]
    if combos:
        for b in combo_specs(version):
            b['pattern']=whole(*(P[s] for s in b['required']),exclude=tuple(P[s] for s in b['excluded'])+tuple(b.get('extra_excluded',())))
            items.append(b)
    rest=['dv-p7','dv-p8','dv-p5','dolby-vision','atmos','truehd','dtsx','dtshd','dtshd-core','ddplus','dd','hdr10plus','hdr10','hlg','hdr','sdr','imax-enhanced','imax','71','61','51','20','10','10bit','8bit','av1','hevc','avc','vp9','flac','pcm','opus','aac','mp3','dts','bluray','web-dl','webrip','hdtv','dvdrip']
    items.extend(data.pop(s) for s in rest if s in data)
    items.extend(data.values())
    for b in items:
        if 'pattern' not in b:b['pattern']=single_rule(b['slug'],version,combos)
    return items

GROUPS=[('resolution','Resolution'),('video-tech','Video Tech'),('audio-tech','Audio Tech'),('source','Source'),('audio-channels','Audio Channels'),('video-codec','Video Codec')]
MAP={'resolution':'resolution','source':'source','video':'video-tech','audio':'audio-tech','channels':'audio-channels','codec':'video-codec','combo':'video-tech','platform':'source','edition':'source','language':'audio-tech'}

def make_config(version,ext=None,combos=True):
    ext=ext or ('svg' if version=='epx' else 'png')
    filters=[]
    for b in catalogue(version,combos):
        s=b['slug']; group=MAP[b['category']]
        if b['category']=='combo' and 'dv-' not in s:group='audio-tech'
        display=b['title']+' · '+b['subtitle'] if b['category']=='combo' or s.startswith('dv-p') or s in ['dtshd','dtshd-core','imax-enhanced'] else b['title']
        filters.append(dict(id='ly8-'+s,groupId=group,name=display,pattern=b['pattern'],imageURL=f'{BASE}/{version}/{ext}/{s}.{ext}',tagColor='#00000000',borderColor='#00000000',textColor='#00000000',tagStyle='filled',isEnabled=True,type='filter'))
    return dict(filters=filters,groups=[dict(id=i,name=n,color='#00000000',borderColor='#00000000',isExpanded=True) for i,n in GROUPS])

def write_configs():
    for filename,ver,ext,combos in [
        ('Badge LiangYou Ver.EPX.json','epx','svg',True),('Badge LiangYou Ver.all.json','all','png',True),
        ('Badge LiangYou Ver.EPX8.json','epx','svg',True),('Badge LiangYou Ver.all8.json','all','png',True),
        ('Badge LiangYou Ver.EPX.PNG.json','epx','png',True),('Badge LiangYou Ver.all.Single.json','all','png',False)]:
        (ROOT/filename).write_text(json.dumps(make_config(ver,ext,combos),ensure_ascii=False,indent=2)+'\n')
    diagnostic={'filters':[dict(id='ly8-size-test',groupId='resolution',name='良友尺寸诊断',pattern=r'(?s)\A[\s\S]*',imageURL=f'{BASE}/epx/png/size-test.png',tagColor='#00000000',borderColor='#00000000',textColor='#00000000',tagStyle='filled',isEnabled=True,type='filter')], 'groups':[dict(id='resolution',name='Resolution',color='#00000000',borderColor='#00000000',isExpanded=True)]}
    (ROOT/'Badge LiangYou Diagnostic.json').write_text(json.dumps(diagnostic,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    # UHD Blu-ray is a conjunction rather than a simple token.
    P['uhd-bluray']=P['bluray']
    write_configs()
    print({v:len(catalogue(v)) for v in ['epx','all']})

# Also define it for imports by the renderer and test runner.
P['uhd-bluray']=P['bluray']
