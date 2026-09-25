"""Regression checks against the JSON actually delivered to players."""
import itertools
import json
import re
import time
from pathlib import Path
from PIL import Image
from lxml import etree
import compact_badges as c
from test_badges import ICU

CASES = [
    ('Movie.2160p.UHD.BluRay.REMUX.DV.TrueHD.Atmos.7.1.HEVC.10bit 中文音轨 英语音轨',
     '4k combo-uhd-remux-truehd combo-dv-atmos combo-hevc-10bit 71 audio-chinese-english'),
    ('Movie.1080p.BluRay.DTS-HD.MA.5.1.H264.8bit',
     '1080p combo-bluray-dtshd combo-avc-8bit 51'),
    ('Movie.2160p.WEB-DL.DV.DDP5.1.H265.10bit Audio: chi,eng',
     '4k combo-web-dl-ddplus combo-dv-atmos combo-hevc-10bit 51 audio-chinese-english'),
    ('Movie.720p.WEBRip.AAC2.0.H264.8bit', '720p combo-webrip-aac combo-avc-8bit 20'),
    ('Movie.480p.DVDRip.XviD.MP3.8bit', '480p combo-dvdrip-mp3 combo-xvid-8bit'),
    ('UHD Blu-ray REMUX TrueHD', '4k combo-uhd-remux-truehd hevc'),
    ('UHD Blu-ray TrueHD', '4k combo-uhd-bluray-truehd hevc'),
    ('REMUX TrueHD', 'combo-remux-truehd'),
    ('BluRay DTS-HD HRA', 'combo-bluray-dtshd-core'),
    ('BluRay DTS-HD MA', 'combo-bluray-dtshd'),
    ('BluRay DTS:X', 'combo-bluray-dtsx'),
    ('BluRay DTS', 'combo-bluray-dts'),
    ('BluRay LPCM', 'combo-bluray-pcm'),
    ('BluRay FLAC', 'combo-bluray-flac'),
    ('WEB-DL E-AC-3', 'combo-web-dl-ddplus'),
    ('WEB-DL DD+', 'combo-web-dl-ddplus'),
    ('WEB-DL AC-3', 'combo-web-dl-dd'),
    ('WEBRip OPUS', 'combo-webrip-opus'),
    ('HDTV AAC', 'combo-hdtv-aac'),
    ('DVDRip MP3', 'combo-dvdrip-mp3'),
    ('WEB-DL TrueHD', 'web-dl truehd'),  # uncommon pair keeps both known facts
    ('REMUX', 'remux'),
    ('UHD Blu-ray REMUX', '4k uhd-remux hevc'),
    ('BluRay', 'bluray'),
    ('WEB-DL', 'web-dl'),
    ('TrueHD', 'truehd'),
    ('TrueHD 7.1', 'truehd 71'),  # TrueHD alone must not become Atmos
    ('Dolby Vision Atmos', 'combo-dv-atmos hevc'),
    ('Atmos', 'atmos'),
    ('Dolby Vision', 'dolby-vision hevc'),
    ('DV TrueHD 5.1', 'dolby-vision truehd 51 hevc'),
    ('DTS-HD MA', 'dtshd'),
    ('DTS-HD HRA', 'dtshd-core'),
    ('dca profile: DTS-HD MA', 'dtshd'),
    ('dca profile: HRA', 'dtshd-core'),
    ('dca profile: X', 'dtsx'),
    ('dca', 'dts'),
    ('PCM_S24LE', 'pcm'),
    ('A_PCM/INT/LIT', 'pcm'),
    ('Sample_Format=fltp', 'pcm'),  # inherited fallback with no encoded codec
    ('Audio Codec: AAC Sample_Format=fltp', 'aac'),
    ('Audio Codec: EAC3 Sample_Format=fltp', 'ddplus'),
    ('BluRay AAC Sample_Format=fltp', 'combo-bluray-aac'),
    ('HEVC 10bit', 'combo-hevc-10bit'),
    ('HEVC H.265 x265 10bit', 'combo-hevc-10bit'),
    ('H.264 AVC 8bit', 'combo-avc-8bit'),
    ('AV1 Main10 10bit', 'combo-av1-10bit'),
    ('VP9 10bit', 'combo-vp9-10bit'),
    ('VC-1 8bit', 'combo-vc1-8bit'),
    ('MPEG-2 8bit', 'combo-mpeg2-8bit'),
    ('DivX 8bit', 'combo-divx-8bit'),
    ('HEVC 10bit 8bit', 'combo-hevc-10bit'),
    ('HEVC', 'hevc'),
    ('AVC', 'avc'),
    ('Main10', 'hevc'),  # existing HEVC fallback; no invented bit-depth badge
    ('10bit', '10bit'),
    ('8bit', '8bit'),
    ('HEVC Video BitDepth=10', 'combo-hevc-10bit'),
    ('AVC Video BitDepth=8', 'combo-avc-8bit'),
    ('HEVC Audio BitDepth=24', 'hevc'),
    ('PCM_S16LE', 'pcm'),
    ('L5.1', ''),
    ('Level 5.1', ''),
    ('Profile 5.1', ''),
    ('HEVC Level 5.1 AAC 2.0', 'aac hevc 20'),
    ('AAC2.0', 'aac 20'),
    ('DDP5.1', 'ddplus 51'),
    ('Stereo Audio', '20'),
    ('Mono Audio', '10'),
    ('Audio Channels: 2', '20'),
    ('Audio Channels: 1', '10'),
    ('8ch', ''),
    ('6ch', ''),
    ('Version 2.0', ''),
    ('60fps 120fps', '120fps'),
    ('中文字幕 英文字幕', ''),
    ('English subtitles Japanese subtitles', ''),
    ('Audio: eng; subtitles: jpn', 'english'),
    ('Audio Language: jpn\nSubtitle Language: eng', 'japanese'),
    ('Audio: chi,eng', 'audio-chinese-english'),
    ('音轨：中文、英语', 'audio-chinese-english'),
    ('中英音轨', 'audio-chinese-english'),
    ('中英日音轨', 'audio-chinese-english-japanese'),
    ('中英日韩音轨', 'audio-chinese-english-japanese-korean'),
    ('中文音轨+英语音轨+日语音轨', 'audio-chinese-english-japanese'),
    ('Audio: und', ''),
    ('Audio: eng\n中文配音', 'audio-chinese-english'),
    ('eng', 'english'),
    ('chi', 'chinese'),
]

for alias in ['HEVC', 'H.265', 'H265', 'x265', 'hvc1', 'hev1']:
    CASES.append((alias + ' 10bit', 'combo-hevc-10bit'))
for alias in ['10-bit', '10 bits', 'p010', 'p010le', 'yuv420p10le', 'yuv422p10le']:
    CASES.append(('HEVC ' + alias, 'combo-hevc-10bit'))
for count in range(1, 5):
    for subset in itertools.combinations(['chinese', 'english', 'japanese', 'korean'], count):
        text = ' '.join(s + ' audio' for s in subset)
        slug = subset[0] if count == 1 else 'audio-' + '-'.join(subset)
        CASES.append((text, slug))
for sep in [' ', '\n', '\r\n', '_', '.']:
    CASES.append((sep.join(['1080p', 'BluRay', 'DTS-HD MA', 'H264', '8bit']),
                  '1080p combo-bluray-dtshd combo-avc-8bit'))


def run():
    start = time.monotonic()
    config = json.loads((c.ROOT / c.CONFIGS[0]).read_text())
    for filename in c.CONFIGS:
        assert json.loads((c.ROOT / filename).read_text()) == config, filename
    assert config == c.build()[0], 'generator drift'
    fs = config['filters']
    assert fs[0]['id'] == 'ly10-4k'
    assert config['groups'][0]['id'] == 'resolution'
    ids = [f['id'] for f in fs]
    assert len(ids) == len(set(ids)), 'duplicate IDs'
    group_order = {g['id']: i for i, g in enumerate(config['groups'])}
    assert [group_order[f['groupId']] for f in fs] == sorted(group_order[f['groupId']] for f in fs)
    icu = ICU()
    failures = []
    for text, expected in CASES:
        for engine, matcher in [('Python', lambda p, s: bool(re.search(p, s))), ('ICU', icu.matches)]:
            found = sorted(f['id'][5:] for f in fs if matcher(f['pattern'], text))
            if found != sorted(expected.split()):
                failures.append(dict(engine=engine, text=text, expected=expected, actual=found))
    if failures:
        print(json.dumps(failures, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    # Real split-field limit: broad playback fallbacks and perfect global
    # de-duplication cannot both be implemented by stateless JSON regex alone.
    fields = ['UHD Blu-ray REMUX TrueHD', 'TrueHD', 'HEVC 10bit', 'HEVC',
              '中文音轨 英语音轨', '中文音轨', '英语音轨']
    union = sorted({f['id'][5:] for f in fs if any(icu.matches(f['pattern'], t) for t in fields)})
    assert {'combo-uhd-remux-truehd', 'truehd', 'combo-hevc-10bit', 'hevc',
            'audio-chinese-english', 'chinese', 'english'} <= set(union)

    for f in fs:
        path = c.ROOT / f['imageURL'].split('/main/', 1)[1]
        with Image.open(path) as im:
            im.load()
            assert im.size == (960, 288), (path, im.size)
            assert im.mode == 'RGBA', (path, im.mode)
    for asset in c.build()[1]:
        path = c.ASSETS / 'svg' / (asset['slug'] + '.svg')
        root = etree.parse(str(path)).getroot()
        assert root.attrib['viewBox'] == '0 0 320 96'
        assert not root.xpath('//*[local-name()="text"]'), path
        labels = root.xpath('//@aria-label')
        assert asset['title'] in labels and asset['subtitle'] in labels, path

    perf_start = time.monotonic()
    for noise in ['x' * 10000, 'audio subtitles codec profile ' * 180]:
        for f in fs: icu.matches(f['pattern'], noise)
    report = dict(passed=True, cases=len(CASES), engines=['Python re', 'ICU'],
        assertions=len(CASES) * 2, filters=len(fs), new_assets=len(c.build()[1]),
        elapsed_seconds=round(time.monotonic() - start, 3),
        noise_seconds=round(time.monotonic() - perf_start, 3),
        group_and_filter_order_verified=True, aliases_identical=True,
        all_pngs_decoded=True, all_new_svg_text_outlined=True,
        split_candidate_union_example=union, global_exclusion_guaranteed=False,
        device_tested=False)
    (c.ROOT / 'reports/compact-validation-v10.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__': run()
