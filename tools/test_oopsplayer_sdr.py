"""SDR combinations, standalone fallbacks and cross-candidate regressions."""
import itertools
import json

from oopsplayer_badges import ROOT, DEST, SOURCE
from oopsplayer_markers import encoded
from oopsplayer_sdr import SDR_ID
from oopsplayer_webdl import logical_id
from test_badges import ICU


def run():
    cfg = json.loads(DEST.read_text())
    original = json.loads(SOURCE.read_text())
    icu = ICU()
    checked = 0

    def matched(data, text):
        ids = [logical_id(f['id']) for f in data['filters']
               if icu.matches(f['pattern'], text)]
        assert len(ids) == len(set(ids)), ('overlapping routes', repr(text), ids)
        return ids

    def check(text, expected):
        nonlocal checked
        got = matched(cfg, text)
        want = ['ly12-' + s for s in expected.split()]
        assert got == want, (repr(text), want, got)
        checked += 1

    # Expected lists are independent of the generator's Boolean expressions.
    text_cases = [
        ('SDR', ''),
        ('standard dynamic range', ''),
        ('SDR AAC', 'aac'),
        ('SDR WEB-DL', ''),
        ('SDR WEB-DL AAC', 'combo-web-dl-aac'),
        ('1080p SDR', 'combo-1080p-sdr'),
        ('720p SDR', 'combo-720p-sdr'),
        ('1920x1080 SDR', 'combo-1080p-sdr'),
        ('1280x720 SDR', 'combo-720p-sdr'),
        ('4K SDR', '4k sdr'),
        ('3840x2160 SDR', '4k sdr'),
        ('576p SDR', '576p sdr'),
        ('480p SDR', '480p sdr'),
        ('1080p WEB-DL SDR', 'combo-1080p-web-dl sdr'),
        ('4K WEB-DL SDR', 'combo-4k-web-dl sdr'),
        ('720p WEB-DL SDR', 'combo-720p-sdr web-dl'),
        ('720p WEB-DL SDR AAC', 'combo-720p-sdr combo-web-dl-aac'),
        ('4K HDR10 SDR', '4k hdr10'),
        ('4K HDR10+ SDR', '4k hdr10plus'),
        ('4K DV SDR', '4k dolby-vision hevc'),
        ('1080p HLG SDR', '1080p hlg'),
        ('720p HDR SDR', '720p hdr'),
        ('1080p SDR AAC 2.0 HEVC 中英日韩音轨',
         'combo-1080p-sdr aac 20 hevc audio-chinese-english-japanese-korean'),
    ]
    for text, want in text_cases:
        for separator in [' ', '.', '_', '\n', '\r\n', '\r', '\u0085', '\u2028', '\u2029']:
            check(text.replace(' ', separator), want)

    marker_cases = [
        ([15], ''),
        ([13, 15], 'combo-1080p-sdr'),
        ([14, 15], 'combo-720p-sdr'),
        ([12, 15], '4k sdr'),
        ([2, 13, 15], 'combo-1080p-web-dl sdr'),
        ([2, 12, 15], 'combo-4k-web-dl sdr'),
        ([2, 14, 15], 'combo-720p-sdr web-dl'),
        ([12, 15, 17], '4k hdr10'),
        ([12, 15, 19], '4k dolby-vision hevc'),
    ]
    for ns, want in marker_cases:
        for order in itertools.permutations(ns):
            check(encoded(order), want)

    # These reproduce a mechanism consistent with the screenshot; the
    # screenshot is not a capture of OopsPlayer's actual matcher inputs.
    fragments = ['SDR', 'sdr', 'standard dynamic range', 'Standard_Dynamic_Range',
                 'Video Range: SDR', 'SDR AAC', 'SDR HEVC', encoded([15]),
                 encoded([15, 3, 35, 42, 78, 127])]
    union_results = []
    for name, full in [
        ('1080p-screenshot-facts', text_cases[-1][0]),
        ('720p-text', '720p SDR'),
        ('1080p-markers', encoded([13, 15])),
        ('720p-markers', encoded([14, 15])),
    ]:
        base = matched(cfg, full)
        assert any(i in base for i in ('ly12-combo-1080p-sdr', 'ly12-combo-720p-sdr'))
        for fragment in fragments:
            candidates = [full, fragment]
            ids = list(dict.fromkeys(logical_id(f['id']) for f in cfg['filters']
                       if any(icu.matches(f['pattern'], t) for t in candidates)))
            assert SDR_ID not in ids, (name, repr(fragment), ids)
            assert all(i in ids for i in base), (name, ids, base)
            checked += 1
        union_results.append(dict(name=name, partial_candidates=len(fragments),
                                  base_badges=base, standalone_sdr=False))

    # A WEB-DL combination does NOT consume SDR. Preserve that independent
    # badge, including when the app also provides a source-only candidate.
    for full in ['4K SDR', '1080p WEB-DL SDR', '4K WEB-DL SDR',
                 '576p SDR', '480p SDR', encoded([12, 15]), encoded([2, 13, 15])]:
        assert SDR_ID in matched(cfg, full)
        assert matched(cfg, 'SDR') == []
        checked += 1

    before = list(dict.fromkeys(matched(original, text_cases[-1][0]) + matched(original, 'SDR')))
    assert 'ly12-combo-1080p-sdr' in before and SDR_ID in before

    report = dict(passed=True, date='2026-10-08', assertions=checked, engine='ICU',
                  screenshot_observed=['1080P SDR combination', 'standalone SDR'],
                  screenshot_input_captured=False, original_reproduction=before,
                  candidate_union_cases=union_results,
                  sparse_candidate_policy='Standalone SDR requires resolution in the same candidate.',
                  legitimate_sdr_singles_preserved=['4K SDR', '1080P WEB-DL SDR', '4K WEB-DL SDR', '576P SDR', '480P SDR'],
                  all_combination_rules_unchanged=True,
                  remaining_limit='Stateless JSON cannot resolve arbitrary conflicting metadata across independent candidates.',
                  device_tested=False)
    (ROOT / 'reports/oopsplayer-sdr-validation.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    run()
