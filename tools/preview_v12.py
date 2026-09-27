"""Preview the actual new assets and resulting badge order."""
import argparse
import json
import re
from PIL import Image, ImageDraw, ImageFont
import portable_badges as p
from v12_badges import COMBOS, PLATFORMS, ASSET_DIR


def render(font_path):
    font = lambda n: ImageFont.truetype(font_path, n)
    im = Image.new('RGB', (1500, 1500), '#0B1220')
    d = ImageDraw.Draw(im)
    d.text((60, 32), 'LIANGYOU / MEDIA BADGES', font=font(22), fill='#97CDEC')
    d.text((60, 76), '良友徽章 · 新组合与平台黑框', font=font(46), fill='#F1F5FC')
    d.text((62, 150), '沿用原有图形 · 声道先于编码 · 平台在音轨前 · 音轨最后', font=font(24), fill='#A8B9CC')

    def badge(path, x, y, width=440):
        with Image.open(path) as src:
            b = src.convert('RGBA').resize((width, round(width * .3)), Image.Resampling.LANCZOS)
            im.paste(b, (x, y), b)

    d.text((60, 213), '01   六种组合', font=font(28), fill='#E6EFFA')
    for i, b in enumerate(COMBOS):
        badge(ASSET_DIR / 'png' / (b['slug'] + '.png'), 60 + i % 3 * 470, 270 + i // 3 * 155)
    d.text((60, 605), '02   平台 · 黑色边框', font=font(28), fill='#E6EFFA')
    for i, slug in enumerate(PLATFORMS):
        badge(ASSET_DIR / 'png' / (slug + '.png'), 60 + i % 3 * 470, 660 + i // 3 * 150)
    d.text((60, 1140), '03   完整排列示例', font=font(28), fill='#E6EFFA')
    text = '4K NF WEB-DL DV TrueHD 7.1 HEVC 10bit 中英双语'
    config = json.loads((p.ROOT / 'Badge LiangYou Ver.all.json').read_text())
    fs = [f for f in config['filters'] if re.search(f['pattern'], text)]
    assert len(fs) == 6, [f['id'] for f in fs]
    for i, f in enumerate(fs):
        badge(p.ROOT / f['imageURL'].split('/main/', 1)[1], 60 + i * 232, 1205, 220)
    d.text((60, 1312), '良友4K WEB-DL → DV +TrueHD → 7.1 → HEVC 10bit → Netflix → 中英音轨', font=font(23), fill='#B5C6D9')
    d.text((60, 1390), '良哥看未来', font=font(24), fill='#93AAC3')
    d.text((1240, 1390), '2026.09.26', font=font(24), fill='#93AAC3')
    out = p.ROOT / 'previews/Complex-New-Combinations-v12.png'
    im.save(out, optimize=True)

    # Check the new frame colors against light and dark UI surfaces.
    im = Image.new('RGB', (1500, 570), '#0B1220')
    im.paste('#F5F6F8', (0, 285, 1500, 570))
    d = ImageDraw.Draw(im)
    for y, color in [(25, '#DDE7F4'), (310, '#172538')]:
        d.text((40, y), '良友4K WEB-DL / 1080P WEB-DL / DV +TrueHD / HDR10 TrueHD / Netflix', font=font(24), fill=color)
        for i, slug in enumerate(['combo-4k-web-dl', 'combo-1080p-web-dl', 'combo-dv-truehd', 'combo-hdr10-truehd', 'netflix']):
            badge(ASSET_DIR / 'png' / (slug + '.png'), 40 + i * 292, y + 85, 276)
    im.save(p.ROOT / 'previews/Complex-Themes-v12.png', optimize=True)
    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--font', required=True)
    args = parser.parse_args()
    print(render(args.font))
