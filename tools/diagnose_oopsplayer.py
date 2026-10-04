"""Build a separate, visible probe pack; never rewrite a production badge pack.

Run with the screenshot's unchanged preview filename, then compare the visible
labels with reports/OOPSPLAYER-DIAGNOSIS.md. No device input is assumed here.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from test_badges import ICU

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'Badge LiangYou Ver.all12.json'
OOPS = ROOT / 'Badge LiangYou Ver.OopsPlayer.json'
DEST = ROOT / 'Badge LiangYou Ver.OopsPlayer.Diagnostic.json'
SAMPLE = 'Example.2160p.BluRay.Remux.DV.TrueHD.Atmos.7.1.mkv'
EXPECTED = [
    'ly12-4k', 'ly12-combo-uhd-remux-truehd',
    'ly12-combo-dv-atmos', 'ly12-71', 'ly12-hevc',
]
# Upstream src/protocol.mjs, commit 34591035590d1aed4cf564c145056b0aa864ebd3.
# These IDs describe BetterFormatter; whether OopsPlayer supplies them is the
# question this pack is intended to answer, not an established device fact.
MARKER_IDS = {'Remux': 0, 'BluRay': 1, '4K': 12, 'DV': 19,
              'Atmos': 22, 'TrueHD': 23, '7.1': 32}


def marker(number):
    bits = f'{number:07b}'.translate(str.maketrans('01', '\u200b\u200d'))
    return '\u2063' + bits + '\u2063'


def build(original, optimized):
    by_id = {f['id']: f for f in optimized['filters']}
    escaped = lambda value: ''.join(r'\u%04x' % ord(c) for c in value)
    marker_sample = ''.join(marker(i) for i in MARKER_IDS.values())
    marker_checks = ''.join(r'(?=[\s\S]*' + escaped(marker(i)) + ')'
                            for i in MARKER_IDS.values())
    # Each independent probe gets a separate existing group ID. BF and U63
    # share one group: BF appears first if the client allows only one per group.
    probes = [
        ('loaded', 'D5', r'[\s\S]+', 0, None),
        ('filename', 'RAW', r'Example[.]2160p[.]BluRay[.]Remux[.]DV[.]TrueHD[.]Atmos[.]7[.]1[.]mkv', 1, None),
        ('text', 'TEXT', r'(?i)2160p|BluRay|Remux|TrueHD|Atmos|7[.]1|Dolby[ ._-]*Vision|\bDV\b', 2, None),
        ('framed', 'BF', r'\u2063[\u200b\u200d]{7}\u2063', 3, None),
        ('u2063', 'U63', r'\u2063', 3, None),
        ('lookahead', 'LOOK', r'(?=[\s\S])[\s\S]+', 4, None),
        ('capture', 'CAP', r'^(?=((?=[\s\S]))?)\1[\s\S]*$', 5, None),
        # Always false in ICU: an empty capture inside a failed lookahead did
        # not participate. ECMAScript instead treats this reference as empty.
        ('unset', 'UNSET', r'^(?=((?!))?)\1[\s\S]*$', 6, None),
        ('marker-facts', 'B7', '^' + marker_checks + r'[\s\S]*$', 7, None),
        ('original-4k', 'RULE4K', by_id['ly12-4k']['pattern'], 8, None),
        # Forced image, deliberately independent of media facts. Its presence
        # proves this previously missing image can load; it is not a real badge.
        ('image', 'IMG', r'[\s\S]+', 9, by_id['ly12-combo-uhd-remux-truehd']['imageURL']),
    ]
    groups = copy.deepcopy(original['groups'])
    for g in groups:
        g.update(name='OopsPlayer diagnostic', color='#4ECDC4', borderColor='#00000000')
    filters = []
    for slug, name, pattern, group, image in probes:
        filters.append(dict(id='oops-diag-' + slug, groupId=groups[group]['id'],
            name=name, pattern=pattern, imageURL=image or '', tagColor='#CC163640',
            borderColor='#FF4ECDC4', textColor='#FFFFFFFF',
            tagStyle='filled and bordered', isEnabled=True, type='filter'))
    return dict(filters=filters, groups=groups), marker_sample


def run():
    before = {p: p.read_bytes() for p in [SOURCE, OOPS]}
    original, optimized = (json.loads(before[p]) for p in [SOURCE, OOPS])
    config, encoded = build(original, optimized)
    icu = ICU()
    match_ids = lambda cfg, value: [f['id'] for f in cfg['filters'] if icu.matches(f['pattern'], value)]
    labels = lambda value: [f['name'] for f in config['filters'] if icu.matches(f['pattern'], value)]

    original_ids, optimized_ids = (match_ids(c, SAMPLE) for c in [original, optimized])
    assert original_ids == optimized_ids == EXPECTED
    marker_ids = match_ids(optimized, encoded)
    assert marker_ids == ['ly12-dolby-vision', 'ly12-hevc']
    # A lone 4K marker, with no DV marker at all, reproduces the false DV pair.
    all_marker_results = {str(i): match_ids(optimized, marker(i)) for i in range(78)}
    assert all(ids == marker_ids for ids in all_marker_results.values())
    assert labels(SAMPLE) == ['D5', 'RAW', 'TEXT', 'LOOK', 'CAP', 'RULE4K', 'IMG']
    assert labels(encoded) == ['D5', 'BF', 'U63', 'LOOK', 'CAP', 'B7', 'IMG']
    assert labels('DV') == ['D5', 'TEXT', 'LOOK', 'CAP', 'IMG']
    assert labels('') == []
    assert len({f['id'] for f in config['filters']}) == len(config['filters'])
    assert all(len(f['pattern'].encode()) <= 4096 for f in config['filters'])
    assert all(p.read_bytes() == content for p, content in before.items())
    report = dict(
        date='2026-10-05', status='awaiting_device_diagnostic',
        device_tested=False, cause_confirmed=False,
        sample=SAMPLE, expected_badges=EXPECTED,
        original_result=original_ids, optimized_result=optimized_ids,
        encoded_simulation_result=marker_ids,
        individual_marker_simulations=78,
        upstream_protocol_commit='34591035590d1aed4cf564c145056b0aa864ebd3',
        raw_diagnostic_labels=labels(SAMPLE),
        encoded_diagnostic_labels=labels(encoded),
        dv_only_diagnostic_labels=labels('DV'),
        max_diagnostic_pattern_utf8_bytes=max(len(f['pattern'].encode()) for f in config['filters']),
        protected_files={p.name: hashlib.sha256(b).hexdigest() for p, b in before.items()},
        limitations=[
            'Encoded input is a simulation; no OopsPlayer input was captured.',
            'The probe image is forced and must not be interpreted as a media fact.',
            'The client may truncate, wrap, scroll, or limit tags per group.',
            'MKV is supplied by the player and is absent from this configuration.',
        ])
    DEST.write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n')
    (ROOT / 'reports/oopsplayer-diagnosis.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    run()
