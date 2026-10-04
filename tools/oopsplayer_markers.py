"""Translate BetterFormatter facts into the existing LiangYou Boolean rules.

Protocol: 9mousaa/BetterFormatter, commit
34591035590d1aed4cf564c145056b0aa864ebd3, src/protocol.mjs and src/formatters.mjs.
The upstream Remux marker represents BluRay REMUX; Web represents WEB-DL.
Unrepresented facts (codec, bit depth, platform, etc.) are never invented.
"""
from __future__ import annotations

import re
from functools import lru_cache

from oopsplayer_badges import simplify, memo_pattern

FRAME = '\u2063'
ZERO = '\u200b'
ONE = '\u200d'
FRAME_PATTERN = r'\u2063[\u200b\u200d]{7}\u2063'

# Canonical text is only a specification/testing oracle. The delivered regex
# checks marker codes directly; no transformation support in the app is needed.
CANONICAL = {
    0: 'BluRay REMUX', 1: 'BluRay', 2: 'WEB-DL',
    12: '2160p', 13: '1080p', 14: '720p',
    15: 'SDR', 16: 'HDR', 17: 'HDR10', 18: 'HDR10+', 19: 'DV',
    20: 'IMAX', 21: 'IMAX Enhanced',
    22: 'Atmos', 23: 'TrueHD', 24: 'DD+', 25: 'AC3',
    26: 'DTS:X', 27: 'DTS-HD MA', 28: 'DTS-HD', 29: 'DTS',
    30: '5.1', 31: '6.1', 32: '7.1',
    49: 'English audio', 57: '中文音轨', 58: 'Japanese audio', 59: 'Korean audio',
}


def marker(number):
    if not 0 <= number <= 127:
        raise ValueError(number)
    return FRAME + ''.join(ONE if bit == '1' else ZERO for bit in f'{number:07b}') + FRAME


def encoded(numbers):
    return ''.join(marker(n) for n in numbers)


def decoded(numbers):
    return '\n'.join(CANONICAL[n] for n in numbers if n in CANONICAL)


@lru_cache(None)
def projected(node):
    kind = node[0]
    if kind == 'fact':
        # Every scalar detector is evaluated on the protocol's canonical fact.
        # The AND/OR/NOT tree, including precedence and badge suppression,
        # remains exactly the original source generator's tree.
        rx = re.compile(node[1], re.I)
        matching = [n for n, value in CANONICAL.items() if rx.search(value)]
        return simplify('or', *(('fact', marker(n)) for n in matching))
    if kind in ('true', 'false'):
        return node
    return simplify(kind, *(projected(c) for c in node[1:]))


@lru_cache(None)
def marker_pattern(condition):
    return memo_pattern(projected(condition))


def capture_count(pattern):
    # ICU allows forward references in the existing language collector;
    # Python's parser rejects those, so count with a small regex lexer.
    count = 0
    escaped = bracket = False
    for i, char in enumerate(pattern):
        if escaped:
            escaped = False
        elif char == '\\':
            escaped = True
        elif bracket:
            if char == ']':
                bracket = False
        elif char == '[':
            bracket = True
        elif char == '(' and pattern[i+1:i+2] != '?':
            count += 1
    return count


def dual_pattern(text_pattern, condition):
    marker_rx = marker_pattern(condition)
    # Keep the original text branch's capture numbering. Only the appended
    # marker branch's generated references need an offset.
    count = capture_count(text_pattern)
    marker_body = marker_rx.removeprefix('(?i)')
    marker_body = re.sub(r'\\([1-9][0-9]*)', lambda m: '\\' + str(int(m[1]) + count), marker_body)
    return '(?i)(?:' + text_only_pattern(text_pattern).removeprefix('(?i)') + '|' + marker_body + ')'


def text_only_pattern(pattern):
    body = pattern.removeprefix('(?i)')
    # Simple original rules use search semantics, not a match-at-start API.
    body = body[1:] if body.startswith('^') else '[\\s\\S]*(?:' + body + ')'
    return '(?i)^(?![\\s\\S]*' + FRAME_PATTERN + ')' + body


def adapt(data, conditions):
    """Keep one filter when possible; split exclusive routes for long rules.

    A split filter has exactly the same image, name, group and position as its
    text partner. Only one route can match any one input; the badge's Boolean
    condition is not weakened to meet the per-pattern limit.
    """
    out = []
    for f, condition in zip(data['filters'], conditions):
        combined = dual_pattern(f['pattern'], condition)
        if len(combined.encode('utf-8')) <= 4096:
            out.append(dict(f, pattern=combined))
        else:
            raw = text_only_pattern(f['pattern'])
            structured = marker_pattern(condition)
            assert len(raw.encode('utf-8')) <= 4096, (f['id'], len(raw.encode()))
            out.append(dict(f, pattern=raw))
            out.append(dict(f, id=f['id'] + '-bf', pattern=structured))
    for f in out:
        assert len(f['pattern'].encode('utf-8')) <= 4096, f['id']
        assert len(f['pattern'].encode('utf-16-le')) // 2 <= 4096, f['id']
    return dict(data, filters=out)
