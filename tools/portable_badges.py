"""V11 shared rules for the complex and EplayerX packs.

Only common ICU/ECMAScript regex features; no \\A/\\Z, atomic groups or
recursively embedded complete regexes. All combinations reuse existing assets.
"""
from __future__ import annotations
import argparse
import copy
import functools
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRUE, FALSE = ('true',), ('false',)


def fact(rx): return ('fact', rx)
def NOT(x):
    if x == TRUE: return FALSE
    if x == FALSE: return TRUE
    if x[0] == 'not': return x[1]
    return ('not', x)


def combine(kind, xs):
    identity, zero = (TRUE, FALSE) if kind == 'and' else (FALSE, TRUE)
    flat = []
    for x in xs:
        if x == zero: return zero
        if x == identity: continue
        for y in (x[1:] if x[0] == kind else [x]):
            if y not in flat: flat.append(y)
    if not flat: return identity
    if len(flat) == 1: return flat[0]
    if kind == 'or' and all(x[0] == 'fact' for x in flat):
        return fact('(?:' + '|'.join(x[1] for x in flat) + ')')
    return (kind, *flat)


def AND(*xs): return combine('and', xs)
def OR(*xs): return combine('or', xs)


@functools.lru_cache(None)
def predicate(x):
    kind = x[0]
    if kind == 'true': return ''
    if kind == 'false': return '(?!)'
    if kind == 'fact': return r'(?=[\s\S]*(?:' + x[1] + '))'
    if kind == 'and': return ''.join(predicate(y) for y in x[1:])
    if kind == 'or': return '(?:' + '|'.join(predicate(y) for y in x[1:]) + ')'
    if kind == 'not':
        if x[1][0] == 'fact': return r'(?![\s\S]*(?:' + x[1][1] + '))'
        return '(?!' + predicate(x[1]) + ')'
    raise ValueError(x)


def pattern(x):
    if x[0] == 'fact': return '(?i)' + x[1]
    return '(?i)^' + predicate(x) + r'[\s\S]*$'


def token(s): return r'(?:^|[^a-z0-9])(?:' + s + r')(?![a-z0-9])'
def audio(s): return r'(?:^|[^a-z0-9])(?:' + s + r')(?=$|[^a-z0-9]|[12567][.]\d)'
def T(s): return fact(token(s))
def A(s): return fact(audio(s))


def priority(raw):
    out, previous = {}, []
    for key, value in raw.items():
        out[key] = AND(value, NOT(OR(*previous)))
        previous.append(value)
    return out


def selected_in(raw, allowed):
    """Does the first matching raw fact belong to allowed? Linear expansion."""
    result = FALSE
    for key, value in reversed(list(raw.items())):
        result = OR(value, result) if key in allowed else AND(NOT(value), result)
    return result


LOWRES = T(r'1080[pi]?|fhd|720[pi]?|576[pi]?|480[pi]?')
RES_RAW = {
    '4k': OR(T(r'4k|2160[pi]?|(?:3840|4096)\s*[x×*]\s*\d{3,4}'), fact('超高清'),
        fact(r'(?:video[\s._-]*)?width[\s:="\x27_-]*(?:3840|4096)(?!\d)'),
        AND(T(r'uhd|ultra[\s._-]*hd'), NOT(LOWRES))),
    '1080p': T(r'1080[pi]?|fhd|full[\s._-]*hd|1920\s*[x×*]\s*\d{3,4}'),
    '720p': T(r'720[pi]?|1280\s*[x×*]\s*720'),
    '576p': T(r'576[pi]?|720\s*[x×*]\s*576'),
    '480p': T(r'480[pi]?|(?:720|640)\s*[x×*]\s*480'),
}
RES = priority(RES_RAW)
REMUX = T(r'(?:(?:bd|uhd|blu[\s._-]*ray)[\s._-]*)?remux|rmx')
DISC = T(r'(?<!pcm[_ -])blu[\s._-]*ray|bdrip|brrip|bdmv|bd(?:25|50|66|100)|bdmux|bdremux')
UHD = OR(T(r'(?:uhd|ultra[\s._-]*hd|4k|2160[pi]?)[\s._-]*(?:blu[\s._-]*ray|bd)|(?:blu[\s._-]*ray|bd)[\s._-]*(?:4k|2160[pi]?)|bd(?:66|100)|uhdbd|4kbd'), AND(RES['4k'], DISC))
WEBRIP = T(r'web[\s._-]*rip')
PLATFORM_TAG = T(r'nf|netflix|amzn|amazon|dsnp|disney\+?|atvp|apple[\s._-]*tv\+?|hmax|hbomax|hulu|pmtp|paramount\+?')
WEBDL = OR(T(r'web[\s._-]*(?:dl(?:mux)?|download)|wd'), AND(OR(T('web'), PLATFORM_TAG), NOT(WEBRIP)))
SOURCE_RAW = {'uhd-bluray': UHD, 'bluray': DISC, 'web-dl': WEBDL,
              'webrip': WEBRIP, 'hdtv': T('hdtv'), 'dvdrip': T(r'dvd[\s._-]*rip')}
SOURCE = priority(SOURCE_RAW)


def channels():
    codec = r'(?:true[\s._-]*hd|atmos|ddp|dd\+|e[\s._-]*ac[\s._-]*3|ec3|ac[\s._-]*3|dts(?:[\s._-]*(?:hd|ma|hra|x|hd[\s._-]*ma))*|dca|aac|flac|opus|l?pcm)'
    raw = {}
    for slug, number in [('71', '7.1'), ('61', '6.1'), ('51', '5.1'), ('20', '2.0'), ('10', '1.0')]:
        n = number.replace('.', r'[ ._-]?')
        dotted = number.replace('.', r'\.')
        explicit = fact(r'(?:' + '|'.join([
            r'(?:^|[^a-z0-9])' + codec + r'[\s._:-]*' + n + r'(?!\d)',
            r'(?:audio[\s._-]*channels?|channels?|channel[\s._-]*layout|音频声道|声道)[\s:="\x27]*' + dotted + r'(?!\d)',
            r'(?:^|[^a-z0-9])' + n + r'[\s._-]*(?:ch(?:annels?)?|声道)(?![a-z0-9])',
            r'^\s*' + dotted + r'\s*$',
        ]) + ')')
        if slug in ['71', '61', '51']:
            # A bare surround label is useful in release names, but video
            # Level/Profile 5.1 (with arbitrary whitespace) is not audio.
            video_level = fact(r'(?:level|profile)[\s:="\x27._-]*' + dotted + r'(?!\d)')
            bare = fact(r'(?<![a-z0-9])' + dotted + r'(?![\d.]\d)')
            explicit = OR(explicit, AND(bare, NOT(video_level)))
        else:
            n, word = ('2', 'stereo') if slug == '20' else ('1', 'mono')
            explicit = OR(explicit, T(word + r'(?:[\s._-]*audio)?'), T(n + r'[\s._-]*(?:ch|channels?)'),
                fact(r'(?:audio[\s._-]*channels?|channels?|channel[\s._-]*count|声道)[\s:="\x27_-]*' + n + r'(?![\d.])'))
        raw[slug] = explicit
    return raw


CHANNEL_RAW = channels()
CHANNELS = priority(CHANNEL_RAW)

DV = OR(T(r'dolby[\s._-]*vision|dovi|dv[578]?|dvhe(?:\.\d+(?:\.\d+)?)?|dvh1(?:\.\d+(?:\.\d+)?)?'), fact(r'杜比视界|\u2063'))
ATMOS = OR(A(r'dolby[\s._-]*atmos|atmos|joc'), fact('杜比全景声|全景声'))
DDPLUS = A(r'dolby[\s._-]*digital[\s._-]*plus|e[\s._-]*ac[\s._-]*3|ec[\s._-]*3|ddp|dd\+')
DD_MULTI = fact(r'(?:^|[^a-z0-9])(?:ddp|dd\+|e[\s._-]*ac[\s._-]*3|ec3)[\s._:-]*[57][ ._-]?1(?!\d)')
CH_MULTI = OR(CHANNEL_RAW['71'], CHANNEL_RAW['51'])
# Requested compatibility heuristic: DV + DD+ 5.1/7.1. Ordinary DD+ 5.1,
# 4K DD+ 5.1, and plain DD+ 7.1 never imply Atmos without DV or Atmos/JOC.
DV_DDP_HINT = AND(DV, DDPLUS, OR(DD_MULTI, CH_MULTI))
ATMOS_DISPLAY = OR(ATMOS, DV_DDP_HINT)
DV_ATMOS = AND(DV, ATMOS_DISPLAY)


def dca_profile(rx):
    return AND(T('dca'), fact(r'(?:codec[\s._-]*profile|audio[\s._-]*profile|profile)[\s:="\x27._-]*(?:' + rx + r')(?![a-z0-9])'))


AUDIO_RAW = {
    'truehd': A(r'(?:dolby[\s._-]*)?true[\s._-]*hd|mlp[\s._-]*fba|a[\s._-]*truehd'),
    'dtsx': OR(A(r'dts[:\s._-]*x|dtsx|dca[\s._-]*(?:x|dtsx)'), dca_profile(r'dts[:\s._-]*x|x')),
    'dtshd': OR(A(r'dts[\s._-]*(?:hd[\s._-]*)?(?:ma|master(?:[\s._-]*audio)?|xll)|xll|dca[\s._-]*(?:ma|xll|hdma)'), dca_profile(r'ma|hdma|xll|dts[\s._-]*hd[\s._-]*ma|master[\s._-]*audio')),
    'dtshd-core': OR(A(r'dts[\s._-]*(?:hd(?:[\s._-]*hra)?|hra)|dca[\s._-]*(?:hra|hdhra)'), dca_profile(r'hra|hdhra|high[\s._-]*resolution(?:[\s._-]*audio)?')),
    'pcm': OR(T(r'l?pcm(?:[_-](?:s|u|f)\d+(?:le|be)?)?|linear[\s._-]*pcm|raw[\s._-]*pcm|pcm[_-]*(?:bluray|dvd|alaw|mulaw)|sowt|twos|in24|in32|fl32|fl64'), fact(r'(?:^|[^a-z0-9])a[_-]?pcm(?:[/._-]*(?:int|float|ieee|lit|big))*(?![a-z0-9])')),
    'flac': A('flac'), 'ddplus': DDPLUS,
    'dts': A(r'dts|dca(?:[\s._-]*(?:core|coherent[\s._-]*acoustics))?'),
    'dd': A(r'ac[\s._-]*3|dolby[\s._-]*digital(?![\s._-]*(?:plus|\+))|dd(?![\s._-]*(?:plus|\+))'),
    'opus': A('opus'), 'aac': A(r'aac(?:[\s._-]*(?:latm|lc|he))?|mp4a'), 'mp3': A('mp3'),
}
AUDIO = priority(AUDIO_RAW)
AUDIO['ddplus'] = AND(AUDIO['ddplus'], NOT(ATMOS_DISPLAY))


def selected_audio_in(allowed):
    """Linear-size decision tree; each raw format appears at most twice."""
    result = FALSE
    for a, raw in reversed(list(AUDIO_RAW.items())):
        if a not in allowed:
            result = AND(NOT(raw), result)
        elif a == 'ddplus':
            result = OR(AND(raw, NOT(ATMOS_DISPLAY)), AND(NOT(raw), result))
        else:
            result = OR(raw, result)
    return result


RANGE_RAW = {
    'hdr10plus': OR(fact(r'(?:^|[^a-z0-9])hdr[\s._-]*10[\s._-]*(?:\+|plus|p)(?![a-z0-9])'), fact(r'\u2064')),
    'hdr10': T(r'hdr[\s._-]*10'), 'hlg': T(r'hlg|hybrid[\s._-]*log[\s._-]*gamma'),
    'hdr': T(r'hdr|high[\s._-]*dynamic[\s._-]*range|smpte[\s._-]*2084'),
    'sdr': T(r'sdr|standard[\s._-]*dynamic[\s._-]*range'),
}
RANGES = {s: AND(x, NOT(DV)) for s, x in priority(RANGE_RAW).items()}
IMAX_ENH = T(r'imax[\s._-]*enhanced')

CODEC_RAW = {
    'av1': T(r'av1|av01'),
    'hevc': T(r'hevc|h[\s._-]*265|x265|hvc1|hev1|mpeg[\s._-]*h[\s._-]*part[\s._-]*2'),
    'vp9': T(r'vp9|vp09'),
    'avc': T(r'avc|h[\s._-]*264|x264|avc1|mpeg[\s._-]*4[\s._-]*(?:avc|part[\s._-]*10)'),
    'vc1': T(r'vc[\s._-]*1|wmv3'), 'mpeg2': T(r'mpeg[\s._-]*2(?:video)?'),
    'divx': T('divx'), 'xvid': T('xvid'),
}
CODEC_RAW['hevc'] = OR(CODEC_RAW['hevc'], AND(OR(T(r'main[\s._-]*10'), DV, UHD, AND(RES['4k'], REMUX)),
    NOT(OR(*(x for k, x in CODEC_RAW.items() if k != 'hevc')))))
CODECS = priority(CODEC_RAW)
DEPTH_RAW = {
    '10bit': OR(T(r'10[\s._-]*bits?|10b|hi10p|p010(?:le|be)?|yuv\d+p10(?:le|be)?'), fact(r'(?:video[\s._-]*bit[\s._-]*depth|视频位深)[\s:="\x27]*10(?!\d)')),
    '8bit': OR(T(r'8[\s._-]*bits?|8b|yuv(?:420|422|444)p(?:le|be)?'), fact(r'(?:video[\s._-]*bit[\s._-]*depth|视频位深)[\s:="\x27]*8(?!\d)')),
}
DEPTHS = priority(DEPTH_RAW)


LANG_DATA = [('chinese', '中', r'chi|zho|zh(?:[-_]cn)?|chinese|mandarin', '中文|国语|普通话'),
    ('english', '英', 'eng|en|english', '英文|英语'), ('japanese', '日', 'jpn|ja|japanese', '日文|日语'),
    ('korean', '韩', 'kor|ko|korean', '韩文|韩语')]
LANG_NAMES = '(?:' + '|'.join(x[2] + '|' + x[3] for x in LANG_DATA) + ')'
LANG_GAP = r'[\s:：=\[\]"\x27,，;/+&、.()_-]*'
LANG = {}
for s, short, codes, names in LANG_DATA:
    term = f'(?:{codes}|{names})'
    LANG[s] = fact('(?:' + '|'.join([
        r'(?:audio(?:[\s._-]*(?:languages?|tracks?))?|音轨(?:语言)?|配音)' + LANG_GAP + '(?:' + LANG_NAMES + LANG_GAP + '){0,7}' + term + r'(?![a-z])',
        term + r'[\s._-]*(?:audio|track|音轨|配音)(?![a-z])',
        r'^\s*' + term + r'\s*$',
        r'[中英日韩]{0,3}' + short + r'[中英日韩]{0,3}(?:双语)?(?:音轨|配音)',
    ]) + ')')

ALL_BASE = {Path(f['imageURL']).stem: f for f in json.loads((ROOT / 'tools/fixtures/complex-before-compact.json').read_text())['filters']}
EPX_BASE = {Path(f['imageURL']).stem: f for f in json.loads((ROOT / 'tools/fixtures/epx-before-portable.json').read_text())['filters']}
ASSETS = json.loads((ROOT / 'tools/compact_badge_catalogue.json').read_text())
SOURCE_AUDIO = {}
CODEC_DEPTHS = {}
for b in ASSETS:
    if b['family'] == 'source-audio': SOURCE_AUDIO.setdefault(b['source'], []).append(b['audio'])
    if b['family'] == 'codec-depth': CODEC_DEPTHS.setdefault(b['codec'], []).append(b['depth'])
ASSET_BY = {b['slug']: b for b in ASSETS}
ASSET_BASE = 'https://raw.githubusercontent.com/MaddestAlistar/liangyou-appletv-badges/main/assets/2026-09-25-compact-v10/all/png/'
GROUPS = [('resolution', 'Resolution'), ('master-source', 'Master Source'), ('source', 'Source'),
    ('video-tech', 'Video Tech'), ('audio-tech', 'Audio Tech'), ('edition', 'Edition'),
    ('platform', 'Platform'), ('audio-channels', 'Audio Channels'), ('video-codec', 'Video Codec'),
    ('audio-language', 'Audio Language')]


def source_condition(s):
    if s == 'uhd-remux': return AND(REMUX, UHD)
    if s == 'remux': return AND(REMUX, NOT(UHD))
    return AND(SOURCE[s], NOT(REMUX))


def source_covers_audio(a):
    eligible = {s for s, allowed in SOURCE_AUDIO.items() if a in allowed}
    masters = [s for s in ['uhd-remux', 'remux'] if s in eligible]
    master = REMUX if len(masters) == 2 else OR(*(source_condition(s) for s in masters))
    return OR(master, AND(NOT(REMUX), selected_in(SOURCE_RAW, eligible)))


def build(version='all', combos=True, png=False):
    base = ALL_BASE if version == 'all' else EPX_BASE
    compact = version == 'all' and combos
    out = []

    def add(s, group, condition, asset=False):
        if asset:
            b = ASSET_BY[s]
            template = next(iter(base.values()))
            f = dict(template, imageURL=ASSET_BASE + s + '.png', name=b['title'] + ' · ' + b['subtitle'])
        else:
            if s not in base: return
            f = copy.deepcopy(base[s])
        f.update(id='ly11-' + s, groupId=group, pattern=pattern(condition))
        if png and version == 'epx': f['imageURL'] = f['imageURL'].replace('/svg/', '/png/').removesuffix('.svg') + '.png'
        out.append(f)

    for s, cond in RES.items(): add(s, 'resolution', cond)
    if compact:
        for source in SOURCE_AUDIO:
            group = 'master-source' if source in ['uhd-remux', 'remux'] else 'source'
            source_cond = source_condition(source)
            for a in SOURCE_AUDIO[source]:
                add(f'combo-{source}-{a}', group, AND(source_cond, AUDIO[a]), True)
            if source in ['uhd-remux', 'remux']:
                fallback = AND(source_cond, NOT(selected_audio_in(SOURCE_AUDIO[source])))
                add(source, group, fallback, source == 'uhd-remux')
            else:
                # Blu-ray may coexist with a generic REMUX master badge. A
                # UHD REMUX image already carries UHD Blu-ray information.
                covered = AND(NOT(REMUX), selected_audio_in(SOURCE_AUDIO[source]))
                if source == 'uhd-bluray': covered = OR(covered, REMUX)
                add(source, group, AND(SOURCE[source], NOT(covered)))
    else:
        add('remux', 'master-source', REMUX)
        for s, cond in SOURCE.items(): add(s, 'source', cond)

    add('combo-dv-atmos', 'video-tech', DV_ATMOS)
    add('dolby-vision', 'video-tech', AND(DV, NOT(ATMOS_DISPLAY)))
    for s, cond in RANGES.items(): add(s, 'video-tech', cond)
    add('imax-enhanced', 'video-tech', IMAX_ENH)
    add('imax', 'video-tech', AND(T('imax'), NOT(IMAX_ENH)))
    add('3d', 'video-tech', T(r'3d|hsbs|htab|half[\s._-]*sbs|full[\s._-]*sbs'))
    add('atmos', 'audio-tech', AND(ATMOS_DISPLAY, NOT(DV)))
    for a, cond in AUDIO.items():
        if compact:
            cond = AND(cond, NOT(source_covers_audio(a)))
        add(a, 'audio-tech', cond)

    # Existing labels/styles are preserved; scoped platform rules avoid the
    # movie title "Mad Max" being classified as a Max web source.
    from badge_rules import P
    for s in ['directors-cut', 'extended', 'remastered', 'open-matte', 'repack', 'proper', 'criterion', 'hybrid', 'black-white', 'theatrical']:
        add(s, 'edition', fact(P[s]))
    for s in ['netflix', 'prime-video', 'apple-tv', 'disney-plus', 'max', 'hulu', 'peacock', 'paramount-plus', 'crunchyroll']:
        p = P[s].replace(r'\A', '^').replace(r'\Z', '$')
        add(s, 'platform', fact(p))
    for s, cond in CHANNELS.items(): add(s, 'audio-channels', cond)
    for codec, cond in CODECS.items():
        if compact:
            depths = CODEC_DEPTHS[codec]
            for depth in depths:
                add(f'combo-{codec}-{depth}', 'video-codec', AND(cond, DEPTHS[depth]), True)
            add(codec, 'video-codec', AND(cond, NOT(OR(*(DEPTHS[d] for d in depths)))), codec in ['hevc', 'avc'])
        else:
            add(codec, 'video-codec', cond)
    for depth, cond in DEPTHS.items():
        if compact: cond = AND(cond, NOT(selected_in(CODEC_RAW, {s for s, ds in CODEC_DEPTHS.items() if depth in ds})))
        add(depth, 'video-codec', cond)
    fps = priority({s: fact(P[s]) for s in ['120fps', '60fps', '50fps']})
    for s, cond in fps.items(): add(s, 'video-codec', cond)
    if version == 'all':
        if compact:
            for n in [4, 3, 2]:
                for subset in itertools.combinations(LANG, n):
                    add('audio-' + '-'.join(subset), 'audio-language', AND(*(LANG[s] for s in subset), NOT(OR(*(LANG[s] for s in LANG if s not in subset)))), True)
        for s, cond in LANG.items():
            if compact: cond = AND(cond, NOT(OR(*(LANG[t] for t in LANG if t != s))))
            add(s, 'audio-language', cond)
    return dict(filters=out, groups=[dict(id=s, name=n, color='#00000000', borderColor='#00000000', isExpanded=True) for s, n in GROUPS if any(f['groupId'] == s for f in out)])


ALIASES = {
    'all': ['Badge LiangYou Ver.all.json', 'Badge LiangYou Ver.all9.json', 'Badge LiangYou Ver.all10.json', 'Badge LiangYou Ver.all11.json', 'Badge LiangYou Ver.all.Relaxed.json'],
    'epx': ['Badge LiangYou Ver.EPX.json', 'Badge LiangYou Ver.EPX9.json', 'Badge LiangYou Ver.EPX10.themefix.json', 'Badge LiangYou Ver.EPX11.json', 'Badge LiangYou Ver.EPX.Relaxed.json'],
    'all-single': ['Badge LiangYou Ver.all.Single.json'],
    'epx-png': ['Badge LiangYou Ver.EPX.PNG.json'],
}


def configs():
    return {'all': build('all'), 'epx': build('epx'), 'all-single': build('all', False), 'epx-png': build('epx', png=True)}


def write_configs():
    result = configs()
    for version, names in ALIASES.items():
        text = json.dumps(result[version], ensure_ascii=False, indent=2) + '\n'
        for name in names: (ROOT / name).write_text(text)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render-epx-png', action='store_true', help='Render the existing outlined EplayerX SVG assets with Inkscape')
    args = parser.parse_args()
    result = write_configs()
    if args.render_epx_png:
        from concurrent.futures import ThreadPoolExecutor
        from render_badges import render_png
        jobs = []
        for f in result['epx']['filters']:
            svg = ROOT / f['imageURL'].split('/main/', 1)[1]
            jobs.append((svg, svg.parent.parent / 'png' / (svg.stem + '.png')))
        with ThreadPoolExecutor(max_workers=4) as pool: list(pool.map(render_png, jobs))
    print(json.dumps({v: dict(filters=len(d['filters']), max_pattern=max(len(f['pattern']) for f in d['filters']), bytes=len(json.dumps(d, ensure_ascii=False).encode())) for v, d in result.items()}))


if __name__ == '__main__': main()
