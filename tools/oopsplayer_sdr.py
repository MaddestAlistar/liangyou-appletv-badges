"""Require resolution context for OopsPlayer's standalone SDR fallback.

Keep the original SDR/HDR precedence and resolution combinations. A bare
SDR candidate must not restore a single after another candidate produced
1080P SDR or 720P SDR. Like BF2's WEB-DL adaptation, this deliberately drops
the standalone badge when the candidate contains no resolution information.
"""
from oopsplayer_badges import compact, memo_pattern
from oopsplayer_markers import dual_pattern

SDR_ID = 'ly12-sdr'


def apply_sdr_fallback(data, source, conditions):
    import portable_badges as p
    original = next(c for f, c in zip(source['filters'], conditions)
                    if f['id'] == SDR_ID)
    condition = p.AND(original, p.OR(*p.RES_RAW.values()))
    candidates = [compact(p.pattern(condition)),
                  memo_pattern(condition), memo_pattern(condition, False)]
    text_pattern = min(candidates, key=lambda rx: len(rx.encode('utf-8')))
    pattern = dual_pattern(text_pattern, condition)
    assert len(pattern.encode('utf-8')) <= 4096
    assert len(pattern.encode('utf-16-le')) // 2 <= 4096
    assert sum(f['id'] == SDR_ID for f in data['filters']) == 1
    return dict(data, filters=[dict(f, pattern=pattern) if f['id'] == SDR_ID else f
                              for f in data['filters']])
