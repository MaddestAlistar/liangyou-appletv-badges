"""Compare ordered badges against all12 plus the explicit OopsPlayer policy.

ICU is the target regex dialect. Empty-capture backreferences deliberately
rely on ICU semantics, so this is not an ECMAScript compatibility test.
No player UI or private media server is accessed by this test.
"""
import hashlib
import itertools
import json
import random
import time
from pathlib import Path

from test_badges import ICU
from oopsplayer_badges import ROOT, SOURCE, DEST, FIXED, WEBDL_FIXED, SDR_FIXED, build
from oopsplayer_markers import CANONICAL, encoded, decoded
from oopsplayer_webdl import WEB_ID, logical_id
from oopsplayer_sdr import SDR_ID


def cases():
    yield 'device-preview', 'Example.2160p.BluRay.Remux.DV.TrueHD.Atmos.7.1.mkv'
    original = []
    for name in ['portable-cases', 'audio-metadata-cases', 'display-combo-cases']:
        original.extend(json.loads((ROOT / 'tools/fixtures' / (name+'.json')).read_text()))
    yield from (('curated', c['text']) for c in original)
    # Exercise case folding and newline variants in both engines, not just
    # ASCII movie names. The original ICU result is the equivalence oracle.
    folds = [('ss','ß'), ('ff','ﬀ'), ('fi','ﬁ'), ('fl','ﬂ'), ('st','ﬆ')]
    for c in original:
        t = c['text']
        for before, after in folds:
            if before in t.lower(): yield 'unicode-fold', t.lower().replace(before, after)
        if '\n' in t:
            for sep in ['\r\n', '\r', '\u0085', '\u2028', '\u2029']:
                yield 'newlines', t.replace('\r\n','\n').replace('\n',sep)
    rng = random.Random(20261004)
    parts = [
        ['', '2160p', '1080p', '720p', '576p', '480p', 'UHD', '3840×1600', 'width=4096', '超高清'],
        ['', 'UHD Blu-ray', 'BluRay', 'REMUX', 'WEB-DL', 'WEBRip', 'HDTV', 'DVDRip', 'NF', 'BD100', 'pcm_bluray'],
        ['', 'TrueHD', 'DTS:X', 'DTS-HD MA', 'dca profile=ma', 'dca profile=hra', 'dca profile=x', 'EAC3', 'DD+', 'AAC', 'FLAC', 'LPCM', 'AC3', 'OPUS', 'MP3'],
        ['', 'DV', 'HDR10+', 'HDR10', 'HLG', 'SDR', 'IsAtmos=false', 'TrueHD16-ch', 'JOC', 'DDP5.1', 'Atmos', 'dynamic object count=2'],
        ['', 'AV1', 'HEVC', 'H264', 'Main10', 'VP9', 'VC1', 'MPEG2', 'XviD', 'DivX', '10bit', '8bit'],
        ['', '7.1', '5.1', 'Level 5.1', '2ch', 'mono', 'channels=20', '120fps', '50 fps'],
        ['', 'Audio: chi,eng', 'Audio: jpn,kor', 'Language=eng', '字幕：中英双语', '中文音轨', 'English subtitles'],
    ]
    for _ in range(3500):
        selected = [rng.choice(p) for p in parts]
        if rng.random() < .35: selected += [rng.choice(parts[2]), rng.choice(parts[3])]
        rng.shuffle(selected)
        yield 'mixed', rng.choice([' ', '.', '_', '\n', '\r\n', ' | ']).join(selected)
    aliases = [['zh', 'chi', 'yue', 'zh-Hant-HK', '中文', '粤语', 'cantonese'],
               ['eng', 'en-US', '英语', 'English'], ['jpn', 'ja-JP', '日语', 'Japanese'], ['kor', 'ko-KR', '韩语', 'Korean']]
    for mask in range(16):
        for _ in range(75):
            selected = [rng.choice(aliases[i]) for i in range(4) if mask & (1<<i)]
            rng.shuffle(selected)
            value = rng.choice([',', ' / ', ' + ', '；', '、', '\n', '_']).join(selected)
            text = rng.choice([
                'Audio: {}', 'Audio Languages: {}', 'Language={}', '{}', '{} - FLAC - 2.0',
                '{{"Type":"Audio","Language":"{}"}}', 'Audio\r\nFormat : AAC\r\nLanguage : {}\r\nText\r\nLanguage : jpn',
                'Subtitles: {}', '{{"Type":"Subtitle","Language":"{}"}}',
            ]).format(value)
            if rng.random() < .4: text += '\n{"Type":"Subtitle","Language":"'+rng.choice(sum(aliases, []))+'"}'
            yield 'language', text
    # Every permutation and subset of the four independently scoped tracks.
    for n in range(1,5):
        for subset in itertools.permutations(['中文音轨', 'English audio', '日语音轨', '韩语音轨'], n):
            yield 'language-order', '\r\n'.join(subset)
    for length in [7,8,9,10]:
        yield 'language-boundary', '/'.join(['eng'] * length + ['zh'])
        yield 'language-boundary', 'Audio: ' + '/'.join(['eng'] * length + ['zh'])
    for length in [59,60,61]:
            yield 'mediainfo-boundary', 'Audio\n' + 'Format: AAC\n'*length + 'Language: eng\nText\nLanguage: zh'


def marker_cases():
    # Include the device's plausible Remux-only source representation, not
    # only the overcomplete seven-marker simulation used by diagnostic B7.
    yield 'device-preview-protocol', [0, 12, 19, 22, 23, 32]
    for n in range(128):
        yield 'single-marker', [n]
    for pair in itertools.combinations(CANONICAL, 2):
        yield 'marker-pair', list(pair)
    core = [0, 1, 12, 19, 22, 23, 32]
    for mask in range(1, 1 << len(core)):
        yield 'preview-subset', [n for i, n in enumerate(core) if mask & (1 << i)]
    for mask in range(16):
        languages = [n for i, n in enumerate([49, 57, 58, 59]) if mask & (1 << i)]
        for base in [[], [0, 12, 23], [2, 13, 15, 24, 30]]:
            yield 'marker-language', base + languages
    rng = random.Random(20261005)
    axes = [[None, 0, 1, 2], [None, 12, 13, 14],
            [None, 15, 16, 17, 18, 19], [None, 22, 23, 24, 25, 26, 27, 28, 29],
            [None, 30, 31, 32], [None, 20, 21], [None, 49, 57, 58, 59]]
    for _ in range(1600):
        ns = [n for choices in axes if (n := rng.choice(choices)) is not None]
        ns += rng.sample(list(CANONICAL), rng.randrange(4))
        ns += rng.sample([3, 7, 11, 33, 35, 38, 42, 77, 78, 127], rng.randrange(4))
        rng.shuffle(ns)
        yield 'mixed-markers', ns


def run():
    started = time.monotonic()
    source_bytes = SOURCE.read_bytes()
    old = json.loads(source_bytes)
    new = json.loads(DEST.read_text())
    assert FIXED.read_bytes() == DEST.read_bytes(), 'BF1 alias differs from the primary OopsPlayer entry'
    assert WEBDL_FIXED.read_bytes() == DEST.read_bytes(), 'BF2 alias differs from the primary OopsPlayer entry'
    assert SDR_FIXED.read_bytes() == DEST.read_bytes(), 'BF3 alias differs from the primary OopsPlayer entry'
    assert new == build(), 'Generated file differs from generator'
    assert old['groups'] == new['groups']
    assert len(old['filters']) == 161
    originals = {f['id']: f for f in old['filters']}
    logical_order = list(dict.fromkeys(logical_id(f['id']) for f in new['filters']))
    assert logical_order == list(originals)
    assert len({f['id'] for f in new['filters']}) == len(new['filters'])
    for b in new['filters']:
        a = originals[logical_id(b['id'])]
        assert {k:v for k,v in a.items() if k not in ('pattern', 'id')} == {k:v for k,v in b.items() if k not in ('pattern', 'id')}
        assert len(b['pattern']) <= 4096
        assert len(b['pattern'].encode('utf-8')) <= 4096
        assert len(b['pattern'].encode('utf-16-le')) // 2 <= 4096
    icu = ICU()
    failures = []
    counts = {}
    policy_changes = {i: {'text': 0, 'markers': 0} for i in (WEB_ID, SDR_ID)}
    resolution_ids = {f['id'] for f in old['filters'] if f['groupId'] == 'resolution'}
    def expected_with_policy(ids, kind):
        if not resolution_ids.intersection(ids):
            for badge_id in policy_changes:
                if badge_id in ids:
                    policy_changes[badge_id][kind] += 1
            return [i for i in ids if i not in policy_changes]
        return ids
    unique = set()
    def matched(cfg, text):
        ids = [logical_id(f['id']) for f in cfg['filters'] if icu.matches(f['pattern'], text)]
        assert len(ids) == len(set(ids)), ('duplicate badge', text, ids)
        return ids
    for kind, text in cases():
        if text in unique: continue
        unique.add(text)
        counts[kind] = counts.get(kind,0)+1
        a = matched(old, text)
        expected = expected_with_policy(a, 'text')
        b = matched(new, text)
        if expected != b:
            failures.append(dict(kind=kind,text=text,original=a,expected=expected,optimized=b))
            if len(failures)==10: break
    marker_unique, marker_counts = set(), {}
    for kind, ns in marker_cases():
        key = tuple(ns)
        if key in marker_unique:
            continue
        marker_unique.add(key)
        marker_counts[kind] = marker_counts.get(kind, 0) + 1
        original = matched(old, decoded(ns))
        expected = expected_with_policy(original, 'markers')
        got = matched(new, encoded(ns))
        if expected != got:
            failures.append(dict(kind=kind, marker_ids=ns, canonical=decoded(ns), original=original, expected=expected, optimized=got))
            if len(failures) == 10:
                break
    # Metadata absent from the marker protocol must not become DV or HEVC.
    assert matched(new, encoded([3, 35, 42, 78, 127])) == []
    assert matched(new, encoded([12])) == ['ly12-4k']
    expected_preview = ['ly12-4k', 'ly12-combo-uhd-remux-truehd', 'ly12-combo-dv-atmos', 'ly12-71', 'ly12-hevc']
    assert matched(new, encoded([0, 12, 19, 22, 23, 32])) == expected_preview
    # Framed input selects the protocol route even if a visible description
    # surrounds it. Frame boundaries themselves must never serve as legacy DV.
    assert matched(new, 'visible description ' + encoded([12]) + ' trailing') == ['ly12-4k']
    if failures:
        print(json.dumps(dict(passed=False, cases=len(unique), failures=failures),ensure_ascii=False,indent=2))
        raise SystemExit(1)
    assert SOURCE.read_bytes()==source_bytes
    noise = ['x'*10000, 'audio subtitles codec profile '*180, 'Audio: eng\n'*80 + 'Subtitle: zh\n'*80]
    noise_time = {}
    for name, cfg in [('original',old),('oopsplayer',new)]:
        start = time.monotonic()
        for t in noise:
            for f in cfg['filters']: icu.matches(f['pattern'],t)
        noise_time[name] = round(time.monotonic()-start,3)
    report = dict(passed=True, target='ICU regex / BetterFormatter 7-bit markers', date='2026-10-08',
        badges=161, filters=len(new['filters']),
        split_marker_routes=[f['id'] for f in new['filters'] if f['id'].endswith('-bf')],
        source_git_blob=hashlib.sha1(b'blob '+str(len(source_bytes)).encode()+b'\0'+source_bytes).hexdigest(),
        source_sha256=hashlib.sha256(source_bytes).hexdigest(),
        original_max_characters=max(len(f['pattern']) for f in old['filters']),
        optimized_max_characters=max(len(f['pattern']) for f in new['filters']),
        optimized_max_utf16_units=max(len(f['pattern'].encode('utf-16-le'))//2 for f in new['filters']),
        optimized_max_utf8_bytes=max(len(f['pattern'].encode('utf-8')) for f in new['filters']),
        original_patterns_over_4096=sum(len(f['pattern'])>4096 for f in old['filters']),
        optimized_patterns_over_4096=0, original_file_bytes=len(source_bytes), optimized_file_bytes=DEST.stat().st_size,
        cases=len(unique), cases_by_category=counts,
        marker_cases=len(marker_unique), marker_cases_by_category=marker_counts,
        ordered_result_comparisons=len(unique)+len(marker_unique),
        mismatches=0, metadata_images_order_preserved=True,
        comparison_policy='Original all12 results, except standalone WEB-DL and SDR require a resolution badge in the same candidate.',
        intentional_webdl_suppressions=policy_changes[WEB_ID],
        intentional_sdr_suppressions=policy_changes[SDR_ID],
        device_diagnostic_observed=['D5','BF','U63','LOOK','CAP','forced_image'],
        example_marker_ids=[0,12,19,22,23,32], example_expected_badges=expected_preview,
        original_file_unchanged=True, device_tested=False,
        device_test_note='BF1 preview was confirmed by user screenshots. BF3 adds the SDR fallback change and needs device verification after reimport; it preserves the BF2 WEB-DL rules.',
        noise_seconds=noise_time,
        elapsed_seconds=round(time.monotonic()-started,3))
    (ROOT/'reports').mkdir(exist_ok=True)
    (ROOT/'reports/oopsplayer-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__': run()
