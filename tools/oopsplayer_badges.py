"""Build an additive OopsPlayer variant without writing any original pack."""
from __future__ import annotations

import argparse
import copy
import json
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path
from re import _parser as parser, _constants as C

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'Badge LiangYou Ver.all12.json'
DEST = ROOT / 'Badge LiangYou Ver.OopsPlayer.json'
FIXED = ROOT / 'Badge LiangYou Ver.OopsPlayer.BF1.json'
WEBDL_FIXED = ROOT / 'Badge LiangYou Ver.OopsPlayer.BF2.json'
ANY = r'[\s\S]'


def literal(n, in_class=False):
    c = chr(n)
    if c in '\\' or c in ('[]^-' if in_class else '.^$*+?{}[]()|'):
        return '\\' + c
    if c in '\n\r\t\f\v':
        return {'\n': r'\n', '\r': r'\r', '\t': r'\t', '\f': r'\f', '\v': r'\x0b'}[c]
    if n < 32 or n in (0x2063, 0x2064):
        return r'\u%04x' % n
    return c


CATEGORIES = {C.CATEGORY_DIGIT:r'\d', C.CATEGORY_NOT_DIGIT:r'\D', C.CATEGORY_SPACE:r'\s', C.CATEGORY_NOT_SPACE:r'\S', C.CATEGORY_WORD:r'\w', C.CATEGORY_NOT_WORD:r'\W'}
ANCHORS = {C.AT_BEGINNING:'^', C.AT_END:'$', C.AT_BEGINNING_STRING:r'\A', C.AT_END_STRING:r'\Z', C.AT_BOUNDARY:r'\b', C.AT_NON_BOUNDARY:r'\B'}


@lru_cache(None)
def factor_union(sequences):
    sequences = tuple(dict.fromkeys(sequences))
    if len(sequences) == 1: return ''.join(sequences[0])
    prefix = []
    while all(sequences) and len({s[0] for s in sequences}) == 1:
        prefix.append(sequences[0][0])
        sequences = tuple(s[1:] for s in sequences)
    suffix = []
    while all(sequences) and len({s[-1] for s in sequences}) == 1:
        suffix.insert(0, sequences[0][-1])
        sequences = tuple(s[:-1] for s in sequences)
    def alternate(parts):
        if all(len(s) == 1 and s not in '\\[]^-' for s in parts):
            return '[' + ''.join(parts) + ']'
        if '' in parts and len(parts) == 2:
            return '(?:' + next(s for s in parts if s) + ')?'
        return '(?:' + '|'.join(parts) + ')'
    options = [alternate([''.join(s) for s in sequences])]
    for at in (0, -1):
        grouped = {}
        for s in sequences: grouped.setdefault(s[at] if s else None, []).append(s)
        if 1 < len(grouped) < len(sequences):
            options.append(alternate([factor_union(tuple(v)) for v in grouped.values()]))
    return ''.join(prefix) + min(options, key=lambda s: len(s.encode())) + ''.join(suffix)


def render(seq):
    out = []
    for op, arg in seq:
        if op == C.LITERAL:
            s = literal(arg)
        elif op == C.NOT_LITERAL:
            s = '[^' + literal(arg, True) + ']'
        elif op == C.IN:
            if set(arg) == {(C.CATEGORY, C.CATEGORY_SPACE), (C.CATEGORY, C.CATEGORY_NOT_SPACE)}:
                s = ANY
            elif len(arg) == 1 and arg[0][0] == C.CATEGORY:
                s = CATEGORIES[arg[0][1]]
            else:
                parts = []
                for idx, (k, v) in enumerate(arg):
                    if k == C.NEGATE: parts.append('^')
                    elif k == C.LITERAL: parts.append('-' if v == 45 and idx == len(arg)-1 else literal(v, True))
                    elif k == C.RANGE: parts.append(literal(v[0], True) + '-' + literal(v[1], True))
                    elif k == C.CATEGORY: parts.append(CATEGORIES[v])
                    else: raise ValueError((k, v))
                s = '[' + ''.join(parts) + ']'
        elif op == C.BRANCH:
            s = factor_union(tuple(tuple(render([token]) for token in x) for x in arg[1]))
        elif op == C.SUBPATTERN:
            group, add, delete, body = arg
            assert not add and not delete
            s = '(' + render(body) + ')' if group else render(body)
        elif op in (C.ASSERT, C.ASSERT_NOT):
            direction, body = arg
            s = '(' + ('?<' if direction < 0 else '?') + ('=' if op == C.ASSERT else '!') + unwrap(render(body)) + ')'
        elif op in (C.MAX_REPEAT, C.MIN_REPEAT):
            lo, hi, body = arg
            b = render(body)
            if len(body) != 1 or body[0][0] not in (C.LITERAL, C.NOT_LITERAL, C.IN, C.ANY, C.BRANCH, C.SUBPATTERN) or (body[0][0] == C.BRANCH and len(parser.parse(b)) > 1):
                b = '(?:' + b + ')'
            if (lo, hi) == (0, C.MAXREPEAT): q = '*'
            elif (lo, hi) == (1, C.MAXREPEAT): q = '+'
            elif (lo, hi) == (0, 1): q = '?'
            elif lo == hi: q = '{' + str(lo) + '}'
            else: q = '{' + str(lo) + ',' + ('' if hi == C.MAXREPEAT else str(hi)) + '}'
            s = b + q + ('?' if op == C.MIN_REPEAT else '')
        elif op == C.AT: s = ANCHORS[arg]
        elif op == C.CATEGORY: s = CATEGORIES[arg]
        elif op == C.ANY:
            s = '.'
        elif op == C.GROUPREF: s = '\\' + str(arg)
        else: raise ValueError((op, arg))
        out.append(s)
    return ''.join(out)


def compact(rx):
    return '(?i)' + render(parser.parse(rx))


def unwrap(rx):
    if rx.startswith('(?:') and rx.endswith(')'):
        inside = rx[3:-1]
        try: parser.parse(inside)
        except re.error: pass
        else: return inside
    return rx


def regex_union(expressions):
    return factor_union(tuple(tuple(render([token]) for token in parser.parse(rx)) for rx in expressions))


def top_alternatives(rx):
    """Split only unnested alternatives; character classes and escapes are opaque."""
    depth = 0
    bracket = False
    escaped = False
    start = 0
    parts = []
    for i, ch in enumerate(rx):
        if escaped:
            escaped = False
            continue
        if ch == '\\':
            escaped = True
            continue
        if bracket:
            if ch == ']': bracket = False
            continue
        if ch == '[': bracket = True
        elif ch == '(': depth += 1
        elif ch == ')': depth -= 1
        elif ch == '|' and depth == 0:
            parts.append(rx[start:i])
            start = i + 1
    return parts + [rx[start:]]


def normalize(node):
    kind = node[0]
    if kind == 'fact':
        rx = node[1]
        parts = top_alternatives(rx)
        if len(parts) > 1:
            return simplify('or', *(normalize(('fact', s)) for s in parts))
        if rx.startswith('(?:') and rx.endswith(')'):
            inside = rx[3:-1]
            # A complete non-capturing wrapper, not multiple adjacent groups.
            try:
                parser.parse(inside)
            except re.error:
                pass
            else:
                return normalize(('fact', inside))
        rx = render(parser.parse(rx))
        # Facts only ask whether a match exists. At the beginning of a fact,
        # a consumed start/non-ASCII-alphanumeric delimiter can therefore be
        # expressed as a zero-width left boundary without changing its truth.
        boundary = r'(?:^|[^a-z0-9])'
        if rx.startswith(boundary):
            rx = r'(?<![a-z0-9])' + rx[len(boundary):]
        return ('fact', rx)
    if kind in ('true', 'false'): return node
    return simplify(kind, *(normalize(n) for n in node[1:]))


def simplify(kind, *children):
    if kind == 'not':
        x = children[0]
        if x[0] == 'true': return ('false',)
        if x[0] == 'false': return ('true',)
        if x[0] == 'not': return x[1]
        return ('not', x)
    identity, zero = (('true',), ('false',)) if kind == 'and' else (('false',), ('true',))
    result = []
    for x in children:
        if x == zero: return zero
        if x == identity: continue
        for y in x[1:] if x[0] == kind else [x]:
            if y not in result: result.append(y)
    if any(simplify('not', x) in result for x in result): return zero
    opposite = 'or' if kind == 'and' else 'and'
    result = [x for x in result if not (x[0] == opposite and any(y in result for y in x[1:]))]
    if not result: return identity
    if len(result) == 1: return result[0]
    return (kind, *result)


def children(node):
    return node[1:] if node[0] in ('and', 'or', 'not') else ()


def nnf(node, inverse=False):
    kind = node[0]
    if kind == 'not': return nnf(node[1], not inverse)
    if kind in ('and', 'or'):
        return simplify(('or' if kind == 'and' else 'and') if inverse else kind,
                        *(nnf(n, inverse) for n in node[1:]))
    return simplify('not', node) if inverse else node


def contextual(node, known=None):
    known = known or {}
    if node in known: return ('true',) if known[node] else ('false',)
    kind = node[0]
    if kind not in ('and', 'or', 'not'): return node
    if kind == 'not': return simplify('not', contextual(node[1], known))
    xs = [contextual(n, known) for n in node[1:]]
    result = []
    for i, x in enumerate(xs):
        local = dict(known)
        for j, sibling in enumerate(xs):
            if i == j: continue
            local[sibling] = kind == 'and'
            if sibling[0] == 'not': local[sibling[1]] = kind != 'and'
        result.append(contextual(x, local))
    return simplify(kind, *result)


def memo_pattern(condition, normal_form=True):
    """Cache repeated zero-width truth tests with empty ICU capture flags.

    A positive lookahead is atomic. (?=(P)?) always succeeds, setting
    its empty capture exactly when zero-width P succeeds. A backreference to that
    capture succeeds iff it participated, as required by ICU and Python.
    """
    condition = contextual(normalize(condition))
    if normal_form: condition = nnf(condition)
    for _ in range(8):
        reduced = contextual(condition)
        if reduced == condition: break
        condition = reduced
    selected = set()

    def program(chosen):
        order = []
        def visit(node):
            for c in children(node): visit(c)
            if node in chosen and node not in order: order.append(node)
        visit(condition)
        refs = {n: '\\' + str(i+1) for i, n in enumerate(order)}
        def emit(n, own=False):
            if n in refs and not own: return refs[n]
            k = n[0]
            if k == 'true': return ''
            if k == 'false': return '(?!)'
            if k == 'fact': return '(?=' + ANY + '*' + n[1] + ')'
            if k in ('and', 'or'):
                facts, other = [], []
                for x in n[1:]:
                    if k == 'and' and x[0] == 'not' and x[1][0] == 'fact' and x[1] not in refs:
                        facts.append(x[1][1])
                    elif k == 'or' and x[0] == 'fact' and x not in refs:
                        facts.append(x[1])
                    else: other.append(emit(x))
                if facts: other.insert(0, ('(?!' if k == 'and' else '(?=') + ANY + '*' + regex_union(facts) + ')')
                if k == 'and': return ''.join(other)
                return other[0] if len(other) == 1 else '(?:' + '|'.join(other) + ')'
            if k == 'not':
                if n[1][0] == 'fact' and n[1] not in refs:
                    return '(?!' + ANY + '*' + n[1][1] + ')'
                return '(?!' + emit(n[1]) + ')'
            raise ValueError(n)
        prefix = ''.join('(?=(' + emit(n, True) + ')?)' for n in order)
        return '(?i)^' + prefix + emit(condition) + ANY + '*$'

    counts = Counter()
    def count(node):
        counts[node] += 1
        for c in children(node): count(c)
    count(condition)
    candidates = [n for n, num in counts.items() if num > 1 and n[0] not in ('true','false','not')]
    current = program(selected)
    while candidates:
        options = [(len(program(selected | {n}).encode()), i, program(selected | {n})) for i,n in enumerate(candidates)]
        size, idx, best = min(options)
        if size >= len(current.encode()): break
        selected.add(candidates.pop(idx))
        current = best
    return current


def language_pattern(required):
    """Run the unchanged scoped detector once per distinct language (ICU).

    Each of the four atomic lookaheads records one previously unseen
    language, or takes an empty fallback when none remains. Guards cover
    every capture belonging to that language. After four passes all four
    truth values are known, even when language evidence overlaps in text.
    This uses ICU's retention of participating captures across iterations.
    """
    import portable_badges as p
    small = lambda rx: render(parser.parse(rx))
    names = [s for s, _, _, _ in p.LANG_DATA]
    # 1 is the common subtitle-cue flag. 2..5, 6..9 and 10..13
    # record the four languages through each factored detection route.
    # 14 is the additional Chinese dubbed-edition route.
    slots = {s: [2+i, 6+i, 10+i] + ([14] if i == 0 else []) for i,s in enumerate(names)}
    refs = lambda s: '|'.join('\\' + str(n) for n in slots[s])
    marker = lambda s: '(?!' + refs(s) + ')()'
    terms = '(?:' + '|'.join('(?:' + small(codes+'|'+words) + ')' + marker(s)
                              for s, short, codes, words in p.LANG_DATA) + ')'
    shorts = '(?:' + '|'.join(short + marker(s) for s,short,_,_ in p.LANG_DATA) + ')'
    subtitle = '(?=(' + p.predicate(p.SUBTITLE_CUE) + ')?)'
    subtitle = small(subtitle)
    generic_prefix = r'(?:^|[^a-z0-9])' + p.LANG_KEY + r'["\x27]*[ \t]*[:=：]' + p.LANG_GAP
    prefix = '(?:' + small(p.LANG_PREFIX) + '|(?!\\1)' + small(generic_prefix) + ')'
    value_head = small('(?:' + p.LANG_NAMES + p.LANG_GAP + '){0,7}')
    value_tail = small(r'(?![a-z0-9])(?![ \t._-]*(?:字幕|subtitles?)(?!(?:[a-z]|[ \t]*[:=：])))')
    qualified = prefix + value_head + terms + value_tail
    suffixed = small(r'(?:^|[^a-z0-9])') + terms + small(r'[\s._-]*(?:audio|track|音[轨軌]|配音)(?![a-z])')
    compound = small(r'[中英日韩韓]{0,3}') + shorts + small(r'[中英日韩韓]{0,3}') + '(?:' + small(r'(?:双音轨|雙音軌|音[轨軌]|配音)(?![ \t._-]*(?:字幕|subs?))') + '|(?!\\1)' + small(r'(?:双语|雙語|多语|多語)') + ')'
    dubbed = small(r'(?:国语|國語|粤语|粵語|国配|國配)(?:版|配音)') + marker('chinese')
    detector = '(?:' + '|'.join([qualified, suffixed, compound, dubbed]) + ')'
    collect = '(?:(?=(?:' + ANY + '*' + detector + '|))){4}'
    check = ''.join(('(?=' if s in required else '(?!') + refs(s) + ')' for s in names)
    return '(?i)^' + subtitle + collect + check + ANY + '*$'


def source_conditions():
    import portable_badges as p
    data = json.loads(SOURCE.read_text())
    conditions = []
    original = p.pattern
    def capture(condition):
        conditions.append(condition)
        return original(condition)
    p.pattern = capture
    try:
        assert p.build() == data, 'Source generator drift: review new rules before rebuilding'
    finally:
        p.pattern = original
    return data, conditions


def build_text():
    import portable_badges as p
    data, conditions = source_conditions()
    out = copy.deepcopy(data)
    for f, condition in zip(out['filters'], conditions):
        simple = compact(f['pattern'])
        if f['groupId'] == 'audio-language':
            required = [s for s in p.LANG if s in f['id']]
            f['pattern'] = language_pattern(required)
        else:
            memo = memo_pattern(condition)
            alternative = memo_pattern(condition, False)
            f['pattern'] = min([simple, memo, alternative], key=lambda s:len(s.encode()))
        assert len(f['pattern'].encode('utf-8')) <= 4096, (f['id'], 'UTF-8 limit')
        assert len(f['pattern'].encode('utf-16-le')) // 2 <= 4096, (f['id'], 'UTF-16 limit')
    return out


def build():
    from oopsplayer_markers import adapt
    from oopsplayer_webdl import apply_webdl_fallback
    data, conditions = source_conditions()
    return apply_webdl_fallback(adapt(build_text(), conditions), data, conditions)


if __name__ == '__main__':
    data = build()
    serialized = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    DEST.write_text(serialized)
    FIXED.write_text(serialized)
    WEBDL_FIXED.write_text(serialized)
    print(json.dumps(dict(filters=len(data['filters']), max_characters=max(len(f['pattern']) for f in data['filters']),
                         max_utf8_bytes=max(len(f['pattern'].encode()) for f in data['filters'])), ensure_ascii=False))
