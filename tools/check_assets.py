"""Check v9 assets, actual opacity, theme compositing and configuration targets."""
import json
from urllib.parse import unquote, urlparse
from lxml import etree as ET
from PIL import Image, ImageChops
import badge_rules as rules

root = rules.ROOT
assets = root / 'assets' / rules.VERSION
svgs = sorted(assets.rglob('*.svg'))
pngs = sorted(assets.rglob('*.png'))
assert len(svgs) == len(pngs) == 133
for path in svgs:
    svg = ET.parse(str(path)).getroot()
    assert [svg.get(k) for k in ('width', 'height', 'viewBox')] == ['320', '96', '0 0 320 96'], path
    assert svg.get('preserveAspectRatio') == 'xMidYMid meet', path
    assert not svg.findall('.//{http://www.w3.org/2000/svg}text'), path
    assert not svg.findall('.//{http://www.w3.org/2000/svg}image'), path
    assert not svg.findall('.//{http://www.w3.org/2000/svg}script'), path
    for node in svg.iter():
        for key, value in node.attrib.items():
            if key.endswith('href'):
                assert value.startswith('#'), (path, value)
for path in pngs:
    with Image.open(path) as image:
        image.load()
        assert image.mode == 'RGBA' and image.size == (960, 288), path
        assert image.getchannel('A').getbbox() == (0, 0, 960, 288), path
        # Covers the text and its backdrop; corners intentionally remain rounded.
        box=(120,45,920,245)
        assert image.getchannel('A').crop(box).getextrema() == (255,255), path
        light=Image.alpha_composite(Image.new('RGBA',image.size,'#F5F7FB'),image).convert('RGB')
        dark=Image.alpha_composite(Image.new('RGBA',image.size,'#0A101B'),image).convert('RGB')
        assert ImageChops.difference(light.crop(box),dark.crop(box)).getbbox() is None, path

configs = ['Badge LiangYou Ver.EPX.json', 'Badge LiangYou Ver.all.json',
           'Badge LiangYou Ver.EPX9.json', 'Badge LiangYou Ver.all9.json',
           'Badge LiangYou Ver.EPX.PNG.json', 'Badge LiangYou Ver.all.Single.json',
           'Badge LiangYou Ver.EPX.Relaxed.json', 'Badge LiangYou Ver.all.Relaxed.json',
           'Badge LiangYou Diagnostic.json']
references = 0
for filename in configs:
    data = json.loads((root / filename).read_text())
    assert len({f['id'] for f in data['filters']}) == len(data['filters']), filename
    for f in data['filters']:
        url = urlparse(f['imageURL'])
        assert url.netloc == 'raw.githubusercontent.com', f['imageURL']
        prefix = '/MaddestAlistar/liangyou-appletv-badges/main/'
        assert url.path.startswith(prefix), f['imageURL']
        assert (root / unquote(url.path.removeprefix(prefix))).is_file(), f['imageURL']
        references += 1
for a, b in [('EPX', 'EPX9'), ('all', 'all9')]:
    assert (root / f'Badge LiangYou Ver.{a}.json').read_bytes() == (root / f'Badge LiangYou Ver.{b}.json').read_bytes()
result = dict(passed=True, svg_count=len(svgs), png_count=len(pngs),
              svg_canvas='320x96', png_canvas='960x288',
              external_image_or_font_dependencies=False,
              text_region_alpha=255, text_region_same_on_light_and_dark=True,
              configs=len(configs), local_image_references_checked=references)
(root / 'reports/assets-validation-v9.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
