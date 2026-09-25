"""Validate delivered V11 JSON, including Node semantics and image resources.

The JS adapter maps the pack's leading (?i) to RegExp's i flag. It checks the
portable pattern body; it is not a claim about a particular player's importer.
"""
import json
import re
import subprocess
import time

from PIL import Image
from lxml import etree
import portable_badges as p
from test_badges import ICU

CASES = json.loads((p.ROOT / 'tools/fixtures/portable-cases.json').read_text())


def expand(slugs):
    """Expected single facts from the curated compact-badge expectations."""
    result = set()
    for slug in slugs:
        if slug == 'uhd-remux': result.update(['remux', 'uhd-bluray'])
        elif slug not in p.ASSET_BY: result.add(slug)
        else:
            meta = p.ASSET_BY[slug]
            if meta['family'] == 'source-audio':
                result.add(meta['audio'])
                result.update(['remux', 'uhd-bluray'] if meta['source'] == 'uhd-remux' else [meta['source']])
            elif meta['family'] == 'codec-depth': result.update([meta['codec'], meta['depth']])
            elif meta['family'] == 'language': result.update(meta['languages'])
            else: result.add(slug)
    return result


def run():
    started = time.monotonic()
    configs = {}
    for name, aliases in p.ALIASES.items():
        config = json.loads((p.ROOT / aliases[0]).read_text())
        assert config == p.configs()[name], ('generator drift', name)
        for alias in aliases:
            assert (p.ROOT / alias).read_bytes() == (p.ROOT / aliases[0]).read_bytes(), alias
        configs[name] = config
    icu = ICU()
    patterns = {}
    for name, config in configs.items():
        fs = config['filters']
        assert fs[0]['id'] == 'ly11-4k'
        ids = [f['id'] for f in fs]
        assert len(ids) == len(set(ids))
        groups = {g['id']: n for n, g in enumerate(config['groups'])}
        assert [groups[f['groupId']] for f in fs] == sorted(groups[f['groupId']] for f in fs)
        assert groups['audio-channels'] < groups['video-codec']
        assert groups['master-source'] < groups['source']
        assert all(r'\A' not in f['pattern'] and r'\Z' not in f['pattern'] for f in fs)
        assert max(len(f['pattern']) for f in fs) < 6000
        patterns[name] = [(f['id'][5:], re.compile(f['pattern']), f['pattern']) for f in fs]
    failures = []
    comparisons = 0
    expected_by_pack = {}
    for name in configs:
        available = {s for s, _, _ in patterns[name]}
        expected = [sorted(set(c['expected'].split()) if name == 'all' else expand(c['expected'].split()) & available) for c in CASES]
        expected_by_pack[name] = expected
        for c, want in zip(CASES, expected):
            for engine, matcher in [('Python', lambda rx, raw, t: bool(rx.search(t))), ('ICU', lambda rx, raw, t: icu.matches(raw, t))]:
                got = sorted(s for s, rx, raw in patterns[name] if matcher(rx, raw, c['text']))
                comparisons += 1
                if got != want: failures.append(dict(pack=name, engine=engine, text=c['text'], expected=want, actual=got))

    # Compile every delivered expression once, then compare full semantic results
    # in Node, including scalar playback fields and newline-delimited metadata.
    request = dict(configs=configs, texts=[c['text'] for c in CASES], noise=['x' * 10000, 'audio subtitles codec profile ' * 180])
    proc = subprocess.run(['node', str(p.ROOT / 'tools/portable_regex_check.js')], input=json.dumps(request), text=True, capture_output=True, timeout=45)
    assert proc.returncode == 0, proc.stderr
    node = json.loads(proc.stdout)
    for name, found in node['results'].items():
        for c, want, got in zip(CASES, expected_by_pack[name], found):
            comparisons += 1
            if got != want: failures.append(dict(pack=name, engine='ECMAScript', text=c['text'], expected=want, actual=got))
    if failures:
        print(json.dumps(dict(failed=len(failures), examples=failures[:50]), ensure_ascii=False, indent=2))
        raise SystemExit(1)

    # Same known facts supplied as a release filename or joined playback fields.
    filename = 'Movie.2160p.UHD.BluRay.REMUX.DV.TrueHD.Atmos.7.1.HEVC.10bit 中文音轨 英语音轨'
    playback = '\n'.join(['Video: 3840x2160', 'Source: UHD Blu-ray REMUX', 'Dynamic Range: Dolby Vision',
        'Audio Codec: TrueHD Atmos', 'Audio Channels: 7.1', 'Video Codec: H.265', 'Video BitDepth: 10', 'Audio Languages: chi,eng'])
    fs = configs['all']['filters']
    matches = lambda text: [f['id'][5:] for f in fs if icu.matches(f['pattern'], text)]
    assert matches(filename) == matches(playback)
    assert matches(filename) == ['4k', 'combo-uhd-remux-truehd', 'combo-dv-atmos', '71', 'combo-hevc-10bit', 'audio-chinese-english']

    # No JSON regex can retract a fallback matched against an independent field.
    fields = ['UHD Blu-ray REMUX TrueHD', 'TrueHD', 'HEVC 10bit', 'HEVC', '中文音轨 英语音轨', '中文音轨', '英语音轨']
    union = sorted({s for t in fields for s in matches(t)})
    assert {'combo-uhd-remux-truehd', 'truehd', 'combo-hevc-10bit', 'hevc', 'audio-chinese-english', 'chinese', 'english'} <= set(union)

    images = {f['imageURL'] for config in configs.values() for f in config['filters']}
    for url in images:
        path = p.ROOT / url.split('/main/', 1)[1]
        assert path.is_file(), path
        if path.suffix == '.png':
            with Image.open(path) as im:
                im.load()
                assert im.size == (960, 288) and im.mode == 'RGBA', (path, im.size, im.mode)
        else:
            root = etree.parse(str(path)).getroot()
            assert root.attrib['viewBox'] == '0 0 320 96', path
            assert not root.xpath('//*[local-name()="text"]'), path
    for asset in p.ASSETS:
        path = p.ROOT / 'assets/2026-09-25-compact-v10/all/svg' / (asset['slug'] + '.svg')
        root = etree.parse(str(path)).getroot()
        assert not root.xpath('//*[local-name()="text"]'), path

    perf_started = time.monotonic()
    for text in request['noise']:
        for config in configs.values():
            for f in config['filters']: icu.matches(f['pattern'], text)
    report = dict(passed=True, cases=len(CASES), delivered_variants=len(configs), comparisons=comparisons,
        engines=['Python re', 'ICU', 'Node ECMAScript (leading (?i) mapped to i flag)'],
        filters={k: len(v['filters']) for k, v in configs.items()},
        max_pattern_characters={k: max(len(f['pattern']) for f in v['filters']) for k, v in configs.items()},
        source_aliases_synchronized=True, group_and_filter_order_verified=True,
        scalar_playback_fields_verified=True, joined_metadata_equivalence_verified=True,
        image_urls_checked_locally=len(images), asset_decode_and_svg_checks_passed=True,
        elapsed_seconds=round(time.monotonic() - started, 3),
        noise_icu_seconds=round(time.monotonic() - perf_started, 3), noise_ecmascript_ms=node['noise_ms'],
        split_candidate_union_example=union, global_exclusion_guaranteed=False, device_tested=False)
    (p.ROOT / 'reports/portable-validation-v11.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__': run()
