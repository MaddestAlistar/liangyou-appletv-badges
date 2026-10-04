"""Compare complete ordered badge results against the untouched all12 pack.

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
from oopsplayer_badges import ROOT, SOURCE, DEST, build


def cases():
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


def run():
    started = time.monotonic()
    source_bytes = SOURCE.read_bytes()
    old = json.loads(source_bytes)
    new = json.loads(DEST.read_text())
    assert new == build(), 'Generated file differs from generator'
    assert old['groups'] == new['groups']
    assert len(old['filters']) == len(new['filters']) == 161
    for a, b in zip(old['filters'],new['filters']):
        assert {k:v for k,v in a.items() if k!='pattern'} == {k:v for k,v in b.items() if k!='pattern'}
        assert len(b['pattern']) <= 4096
        assert len(b['pattern'].encode('utf-8')) <= 4096
        assert len(b['pattern'].encode('utf-16-le')) // 2 <= 4096
    icu = ICU()
    failures = []
    counts = {}
    unique = set()
    for kind, text in cases():
        if text in unique: continue
        unique.add(text)
        counts[kind] = counts.get(kind,0)+1
        a = [f['id'] for f in old['filters'] if icu.matches(f['pattern'],text)]
        b = [f['id'] for f in new['filters'] if icu.matches(f['pattern'],text)]
        if a != b:
            failures.append(dict(kind=kind,text=text,original=a,optimized=b))
            if len(failures)==10: break
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
    report = dict(passed=True, target='ICU regex', date='2026-10-04', filters=161,
        source_git_blob=hashlib.sha1(b'blob '+str(len(source_bytes)).encode()+b'\0'+source_bytes).hexdigest(),
        source_sha256=hashlib.sha256(source_bytes).hexdigest(),
        original_max_characters=max(len(f['pattern']) for f in old['filters']),
        optimized_max_characters=max(len(f['pattern']) for f in new['filters']),
        optimized_max_utf16_units=max(len(f['pattern'].encode('utf-16-le'))//2 for f in new['filters']),
        optimized_max_utf8_bytes=max(len(f['pattern'].encode('utf-8')) for f in new['filters']),
        original_patterns_over_4096=sum(len(f['pattern'])>4096 for f in old['filters']),
        optimized_patterns_over_4096=0, original_file_bytes=len(source_bytes), optimized_file_bytes=DEST.stat().st_size,
        cases=len(unique), cases_by_category=counts, ordered_result_comparisons=len(unique),
        individual_pattern_comparisons=len(unique)*161, mismatches=0, metadata_images_order_preserved=True,
        original_file_unchanged=True, device_tested=False, noise_seconds=noise_time,
        elapsed_seconds=round(time.monotonic()-started,3))
    (ROOT/'reports').mkdir(exist_ok=True)
    (ROOT/'reports/oopsplayer-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__': run()
