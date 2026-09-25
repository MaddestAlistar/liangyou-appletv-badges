"""Render exact repository badge assets in a compact preview and full catalogue."""
from pathlib import Path
import argparse
from PIL import Image, ImageDraw, ImageFont
import compact_badges as c


def local_image(url):
    relative = url.split('/main/', 1)[1]
    return c.ROOT / relative


def render(font_path):
    config, assets = c.build()
    filters = {f['id'][5:]: f for f in config['filters']}
    font = lambda n: ImageFont.truetype(font_path, n)

    def canvas(height, title, sub):
        im = Image.new('RGB', (1600, height), '#09111D')
        d = ImageDraw.Draw(im)
        d.text((62, 34), 'LIANGYOU / COMPACT MEDIA BADGES', font=font(22), fill='#85CEF9')
        d.text((62, 78), title, font=font(47), fill='#F1F6FD')
        d.text((64, 146), sub, font=font(23), fill='#A3B4C8')
        return im, d

    def badge(im, slug, x, y, width=346):
        with Image.open(local_image(filters[slug]['imageURL'])) as src:
            b = src.convert('RGBA').resize((width, round(width * .3)), Image.Resampling.LANCZOS)
            im.paste(b, (x, y), b)

    sections = [
        ('01  片源与音频组合', [
            'combo-uhd-remux-truehd', 'combo-uhd-remux-dtshd', 'combo-uhd-bluray-dtsx', 'combo-uhd-bluray-truehd',
            'combo-remux-truehd', 'combo-bluray-dtshd', 'combo-bluray-dtshd-core', 'combo-bluray-pcm',
            'combo-web-dl-ddplus', 'combo-webrip-aac', 'combo-hdtv-dd', 'combo-dvdrip-mp3']),
        ('02  编码与位深组合', [
            'combo-hevc-10bit', 'combo-hevc-8bit', 'combo-avc-10bit', 'combo-avc-8bit',
            'combo-av1-10bit', 'combo-vp9-10bit', 'combo-vc1-8bit', 'combo-mpeg2-8bit']),
        ('03  音轨语言组合', [
            'audio-chinese-english', 'audio-chinese-japanese', 'audio-chinese-korean', 'audio-english-japanese',
            'audio-english-korean', 'audio-japanese-korean', 'audio-chinese-english-japanese', 'audio-chinese-english-japanese-korean']),
    ]
    im, d = canvas(1660, '良友徽章 · 复杂版组合', '保留原有风格 · 组合优先 · 技术信息与音轨靠后')
    y = 215
    for title, slugs in sections:
        d.text((64, y), title, font=font(28), fill='#E2ECF7')
        y += 60
        for i, slug in enumerate(slugs): badge(im, slug, 64 + (i % 4) * 378, y + (i // 4) * 126)
        y += ((len(slugs) + 3) // 4) * 126 + 36
    d.line((64, y, 1536, y), fill='#28394D')
    y += 25
    d.text((64, y), '排列示例  ·  原有 10 枚 → 组合后 6 枚', font=font(26), fill='#E2ECF7')
    slugs = ['4k', 'combo-uhd-remux-truehd', 'combo-dv-atmos', 'combo-hevc-10bit', '71', 'audio-chinese-english']
    for i, slug in enumerate(slugs): badge(im, slug, 64 + i * 248, y + 60, 238)
    d.text((64, 1601), '良哥看未来', font=font(21), fill='#92A8C1')
    d.text((1310, 1601), '2026.09.25', font=font(21), fill='#92A8C1')
    out = c.ROOT / 'previews/Complex-Compact-v10.png'
    im.save(out, optimize=True)

    # All new assets, including every three-language combination and fallbacks.
    rows = (len(assets) + 3) // 4
    im, d = canvas(270 + rows * 126, '复杂版 · 全部新增徽章', f'{len(assets)} 枚原生徽章 · PNG / SVG')
    for i, b in enumerate(assets): badge(im, b['slug'], 64 + (i % 4) * 378, 220 + (i // 4) * 126)
    im.save(c.ROOT / 'previews/Complex-Compact-Catalogue-v10.png', optimize=True)

    # Two surfaces using actual alpha assets, at a small display size.
    im = Image.new('RGB', (1280, 480), '#0B1320')
    im.paste('#F5F6F8', (0, 240, 1280, 480))
    d = ImageDraw.Draw(im)
    for y, color in [(20, '#CAD7E8'), (260, '#15253B')]:
        d.text((24, y), '良友 4K → 片源 → 杜比 → 编码位深 → 声道 → 音轨', font=font(22), fill=color)
        for i, slug in enumerate(slugs): badge(im, slug, 24 + i * 207, y + 65, 196)
    im.save(c.ROOT / 'previews/Complex-Compact-Themes-v10.png', optimize=True)
    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--font', required=True)
    args = parser.parse_args()
    print(render(args.font))
