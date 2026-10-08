"""OopsPlayer-only WEB-DL fallback policy for repeated source candidates.

A stateless regex cannot retract a badge matched against another candidate.
Require resolution context for the standalone WEB-DL badge, while leaving
every combination rule intact. Bare WEB-DL fields/markers no longer add a
second source badge after the player has matched a complete candidate.
"""
from __future__ import annotations

from oopsplayer_badges import memo_pattern
from oopsplayer_markers import marker_pattern, text_only_pattern

WEB_ID = 'ly12-web-dl'
REMUX_ID = WEB_ID + '-text-remux'


def logical_id(filter_id):
    if filter_id == REMUX_ID:
        return WEB_ID
    return filter_id.removesuffix('-bf')


def text_fallback(condition):
    candidates = [text_only_pattern(memo_pattern(condition, form))
                  for form in (True, False)]
    # These source/resolution/audio predicates search for format tokens, not
    # newline characters. DOTALL is safe for their existence tests, including
    # CRLF; do not apply this optimization to the language collector or other
    # rules whose internal newline positions can carry meaning.
    candidates += [rx.replace('(?i)', '(?is)').replace(r'[\s\S]*', '.*')
                   for rx in candidates]
    return min(candidates, key=lambda rx: len(rx.encode('utf-8')))


def apply_webdl_fallback(data, source, conditions):
    import portable_badges as p
    original = next(c for f, c in zip(source['filters'], conditions)
                    if f['id'] == WEB_ID)
    resolution = p.OR(*p.RES_RAW.values())
    low_resolution = p.OR(*(p.RES_RAW[s] for s in ('720p', '576p', '480p')))
    # Without REMUX, the unchanged original condition already excludes 4K
    # and 1080p: those resolutions use a WEB-DL combination. Partition the
    # two exclusive text routes to keep each regex below 4096 bytes.
    plain = p.AND(original, p.NOT(p.REMUX), low_resolution)
    remux = p.AND(original, p.REMUX, resolution)
    structured = p.AND(original, resolution)
    patterns = [(WEB_ID, text_fallback(plain)),
                (REMUX_ID, text_fallback(remux)),
                (WEB_ID + '-bf', marker_pattern(structured))]
    out = []
    for f in data['filters']:
        if f['id'] == WEB_ID:
            for filter_id, pattern in patterns:
                assert len(pattern.encode('utf-8')) <= 4096, filter_id
                assert len(pattern.encode('utf-16-le')) // 2 <= 4096, filter_id
                out.append(dict(f, id=filter_id, pattern=pattern))
        elif f['id'] != WEB_ID + '-bf':
            out.append(f)
    return dict(data, filters=out)
