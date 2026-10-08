"""WEB-DL regression cases, including independent candidates joined by the app."""
import itertools
import json

from oopsplayer_badges import ROOT, DEST, SOURCE
from oopsplayer_markers import encoded
from oopsplayer_webdl import WEB_ID, logical_id
from test_badges import ICU


def run():
    cfg = json.loads(DEST.read_text())
    original = json.loads(SOURCE.read_text())
    icu = ICU()
    checked = 0

    def matched(data, text):
        ids = [logical_id(f['id']) for f in data['filters']
               if icu.matches(f['pattern'], text)]
        assert len(ids) == len(set(ids)), ('overlapping routes', text, ids)
        return ids

    def check(text, expected):
        nonlocal checked
        got = matched(cfg, text)
        want = ['ly12-' + s for s in expected.split()]
        assert got == want, (repr(text), want, got)
        checked += 1

    # Independent expected results, including the intentional sparse-input
    # tradeoff. All WEB-DL combinations retain their original conditions.
    text_cases = [
        ('WEB-DL', ''),
        ('WEB-DL TrueHD', 'truehd'),
        ('WEB-DL AAC', 'combo-web-dl-aac'),
        ('WEB-DL DD+', 'combo-web-dl-ddplus'),
        ('4K WEB-DL', 'combo-4k-web-dl'),
        ('1080p WEB-DL', 'combo-1080p-web-dl'),
        ('720p WEB-DL', '720p web-dl'),
        ('720p WEB-DL SDR', 'combo-720p-sdr web-dl'),
        ('576p WEB-DL', '576p web-dl'),
        ('480p WEB-DL', '480p web-dl'),
        ('1280x720 WEB-DL', '720p web-dl'),
        ('720x576 WEB-DL', '576p web-dl'),
        ('640x480 WEB-DL', '480p web-dl'),
        ('720p WEB-DL AAC', '720p combo-web-dl-aac'),
        ('1080p REMUX WEB-DL TrueHD', '1080p combo-remux-truehd web-dl'),
        ('2160p WEB-DL DV DDP5.1 HEVC DSNP English audio',
         'combo-4k-web-dl combo-dv-atmos 51 hevc disney-plus english'),
    ]
    for text, want in text_cases:
        for separator in [' ', '.', '_', '\n', '\r\n', '\r', '\u0085', '\u2028', '\u2029']:
            check(text.replace(' ', separator), want)

    marker_cases = [
        ([2], ''),
        ([2, 12], 'combo-4k-web-dl'),
        ([2, 13], 'combo-1080p-web-dl'),
        ([2, 14], '720p web-dl'),
        ([2, 14, 15], 'combo-720p-sdr web-dl'),
        ([2, 24], 'combo-web-dl-ddplus'),
        ([2, 12, 19, 22, 30], 'combo-4k-web-dl combo-dv-atmos 51 hevc'),
        ([2, 13, 19, 22, 30], 'combo-1080p-web-dl combo-dv-atmos 51 hevc'),
    ]
    for ns, want in marker_cases:
        for order in itertools.permutations(ns):
            check(encoded(order), want)

    # The report screenshot is not an input capture. These are explicit
    # reproductions of a compatible mechanism: a complete candidate plus
    # independent source-only candidates. Check ordered union, not just one
    # filename, and cover both protocol/text routes in the same candidate set.
    fragments = ['WEB-DL', 'webdl', 'Web DL', 'WEB_DOWNLOAD', 'WD',
                 'Source: WEB-DL', 'DSNP WEB-DL', 'WEB-DL DSNP',
                 encoded([2]), encoded([2, 3, 35, 42, 78, 127])]
    union_results = []
    for name, full in [
        ('4k-playback-screenshot-facts', '2160p WEB-DL DV DDP5.1 HEVC DSNP English audio'),
        ('1080p-text', '1080p WEB-DL'),
        ('web-aac-text', '720p WEB-DL AAC'),
        ('web-ddplus-text', 'WEB-DL DD+'),
        ('4k-markers', encoded([2, 12, 19, 22, 30])),
        ('1080p-markers', encoded([2, 13])),
        ('web-ddplus-markers', encoded([2, 24])),
    ]:
        base = matched(cfg, full)
        assert any(i.startswith('ly12-combo-') and 'web-dl' in i for i in base)
        for fragment in fragments:
            candidates = [full, fragment]
            ids = list(dict.fromkeys(logical_id(f['id']) for f in cfg['filters']
                       if any(icu.matches(f['pattern'], t) for t in candidates)))
            assert WEB_ID not in ids, (name, repr(fragment), ids)
            assert all(i in ids for i in base), (name, ids, base)
            checked += 1
        union_results.append(dict(name=name, source_fragments=len(fragments),
                                  base_badges=base, standalone_webdl=False))

    # Reproduce the reported shape with the unmodified all12 rules. The BF1
    # comparison report already established equivalence for ordinary text.
    full = text_cases[-1][0]
    before = list(dict.fromkeys(matched(original, full) + matched(original, 'WEB-DL')))
    assert 'ly12-combo-4k-web-dl' in before and WEB_ID in before

    # Removing a source-only candidate must not hide valid low-resolution
    # standalone badges; their complete candidate still contains context.
    for full in ['720p WEB-DL', '576p WEB-DL', '480p WEB-DL', encoded([2, 14])]:
        assert WEB_ID in matched(cfg, full)
        assert matched(cfg, 'WEB-DL') == []
        checked += 1

    report = dict(passed=True, date='2026-10-08', assertions=checked,
                  screenshot_observed=['4K WEB-DL combination', 'standalone WEB-DL'],
                  screenshot_input_captured=False, engine='ICU',
                  original_reproduction=before,
                  candidate_union_cases=union_results,
                  sparse_candidate_policy='Standalone WEB-DL requires resolution in the same candidate.',
                  all_combination_rules_unchanged=True,
                  remaining_limit='Stateless JSON cannot resolve arbitrary conflicting metadata across independent candidates.',
                  device_tested=False)
    (ROOT / 'reports/oopsplayer-webdl-validation.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    run()
