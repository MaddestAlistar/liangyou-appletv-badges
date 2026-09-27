"""Native additions to the established complex badge system."""
from pathlib import Path
import argparse
import re
from concurrent.futures import ThreadPoolExecutor
from lxml import etree as ET

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / 'assets/2026-09-26-v12/all'
ASSET_URL = 'https://raw.githubusercontent.com/MaddestAlistar/liangyou-appletv-badges/main/assets/2026-09-26-v12/all/png/'
PLATFORMS = ['netflix', 'prime-video', 'apple-tv', 'disney-plus', 'max', 'hulu', 'peacock', 'paramount-plus', 'crunchyroll']
COMBOS = [
    dict(slug='combo-4k-web-dl', title='良友4K', subtitle='WEB-DL', color='orange', template='4k', facts=['4k', 'web-dl']),
    dict(slug='combo-1080p-web-dl', title='1080P WEB-DL', subtitle='FULL HD · WEB SOURCE', color='purple', template='1080p', facts=['1080p', 'web-dl']),
    dict(slug='combo-dv-truehd', title='DV +TrueHD', subtitle='杜比视界+TrueHD', color='orange', template='dolby-vision', facts=['dolby-vision', 'truehd']),
    dict(slug='combo-hdr10-truehd', title='HDR10 TrueHD', subtitle='静态HDR+TrueHD', color='orange', template='hdr10', facts=['hdr10', 'truehd']),
    dict(slug='combo-1080p-sdr', title='1080P SDR', subtitle='STANDARD RANGE', color='purple', template='1080p', facts=['1080p', 'sdr']),
    dict(slug='combo-720p-sdr', title='720P SDR', subtitle='STANDARD RANGE', color='blue', template='720p', facts=['720p', 'sdr']),
]
for b in COMBOS: b['family'] = 'display-combo'


def render(font):
    import render_badges as renderer
    renderer.set_font(font)
    source = ROOT / 'assets/2026-09-25-v9/all/svg'
    jobs = []
    for b in COMBOS:
        root = ET.parse(str(source / (b['template'] + '.svg'))).getroot()
        edge = root.xpath('//*[local-name()="linearGradient" and @id="edge"]')[0]
        old = [n.get('stop-color') for n in edge if n.get('stop-color') != '#FFFFFF']
        _, light, strong = renderer.PALETTE[b['color']]
        mapping = {old[0]: light, old[1]: strong}
        for n in root.iter():
            for attr in ['fill', 'stroke', 'stop-color']:
                if n.get(attr) in mapping: n.set(attr, mapping[n.get(attr)])
        # Preserve the original resolution/HDR/Dolby icon and the 良 corner.
        # Only the two display labels and their existing frame palette change.
        for n in list(root.xpath('//*[@aria-label]')):
            xy = re.match(r'translate\(([\d.]+)', n.get('transform', ''))
            if xy and float(xy[1]) >= 112: n.getparent().remove(n)
        body = root.xpath('./*[local-name()="g"]')[0]
        size, y = (43.9, 59) if b['template'] == '4k' else (36, 55)
        body.append(renderer.el(renderer.pathtext(b['title'], 124, y, size, '#FFFFFF', maxwidth=219)))
        body.append(renderer.el(renderer.pathtext(b['subtitle'], 124, 82, 22, light, maxwidth=218)))
        jobs.append(write_svg(b['slug'], root))
    for slug in PLATFORMS:
        root = ET.parse(str(source / (slug + '.svg'))).getroot()
        edge = root.xpath('//*[local-name()="linearGradient" and @id="edge"]')[0]
        for stop, color in zip(edge, ['#080808', '#171717', '#3B3B3B', '#171717', '#080808']):
            stop.set('stop-color', color)
        # The restrained inner keyline keeps a black frame visible on dark UI.
        for n in root.xpath('//*[local-name()="rect" and @x="10"]'):
            n.set('stroke', '#777777')
            n.set('stroke-opacity', '.35')
        jobs.append(write_svg(slug, root))
    with ThreadPoolExecutor(max_workers=4) as pool: list(pool.map(renderer.render_png, jobs))
    return len(jobs)


def write_svg(slug, root):
    path = ASSET_DIR / 'svg' / (slug + '.svg')
    path.parent.mkdir(parents=True, exist_ok=True)
    content = ET.tostring(root, encoding='unicode') + '\n'
    if not path.exists() or path.read_text() != content: path.write_text(content)
    return path, ASSET_DIR / 'png' / (slug + '.png')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--font', required=True)
    args = parser.parse_args()
    print('Rendered', render(args.font), 'complex badge assets')
