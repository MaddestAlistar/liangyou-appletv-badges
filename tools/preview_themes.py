"""Native badge layout preview on light and dark surfaces (not an app screenshot)."""
import argparse
from PIL import Image, ImageDraw, ImageFont
import render_badges as render

def build():
    im=Image.new('RGB',(1440,900),'#121B2B');d=ImageDraw.Draw(im)
    font=lambda n:ImageFont.truetype(str(render.FONTFILE),n)
    d.text((40,20),'良友徽章 · 深浅背景预览',font=font(38),fill='#F5F7FC')
    d.text((40,78),'同一套图 · 固定深色底 · 杜比视界+全景声',font=font(22),fill='#B6C6DB')
    slugs=['combo-dv-atmos-truehd','combo-dv-atmos-ddplus','combo-dv-atmos',
           '4k','remux','hevc']
    for x,bg,ink,label in [(24,'#F5F7FB','#182337','浅色界面'),(732,'#0A101B','#EDF3FC','深色界面')]:
        d.rounded_rectangle((x,132,x+684,810),radius=18,fill=bg)
        d.text((x+24,152),label,font=font(30),fill=ink)
        for version,y in [('epx',217),('all',488)]:
            d.text((x+24,y),'EplayerX' if version=='epx' else '复杂版',font=font(25),fill=ink)
            for i,slug in enumerate(slugs):
                p=render.ASSETS/version/'png'/(slug+'.png')
                badge=Image.open(p).convert('RGBA').resize((204,62),Image.Resampling.LANCZOS)
                im.paste(badge,(x+24+(i%3)*212,y+54+(i//3)*84),badge)
    d.text((40,837),'良哥看未来 · 2026.09.25',font=font(19),fill='#AEBED3')
    d.text((666,837),'设计预览；播放器额外施加的透明度仍需实机核对',font=font(19),fill='#AEBED3')
    p=render.ROOT/'previews/Themes-v9.png';im.save(p,optimize=True);print(p)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--font');args=parser.parse_args()
    render.set_font(args.font);build()
