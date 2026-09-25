"""V10 asset renderer and historical rule snapshot; config writes use V11.

The input fixture is the deployed all9 at commit 3b7745e, including playback
fallbacks. Do not reconstruct this pack from the older v9 catalogue generator.
Regex exclusions apply within ONE candidate, not across a client's union of
independently matched fields. No unsupported client-side priority keys are used.
"""
from __future__ import annotations

import argparse
import copy
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = '2026-09-25-compact-v10'
ASSETS = ROOT / 'assets' / VERSION / 'all'
BASE = f'https://raw.githubusercontent.com/MaddestAlistar/liangyou-appletv-badges/main/assets/{VERSION}/all'
CONFIGS = ['Badge LiangYou Ver.all.json', 'Badge LiangYou Ver.all9.json',
           'Badge LiangYou Ver.all10.json']
BASELINE = json.loads((ROOT / 'tools/fixtures/complex-before-compact.json').read_text())
OLD = {Path(f['imageURL']).stem: f for f in BASELINE['filters']}


def bare(pattern):
    return pattern.removeprefix('(?i)')


def scan(pattern):
    p = bare(pattern)
    # Full-candidate predicates already start at offset zero. Wrapping them
    # in another arbitrary-prefix scan multiplies backtracking on long input.
    return p if p.startswith(('\\A', '^')) else r'[\s\S]*?(?:' + p + ')'


def either(*patterns):
    return r'\A(?:' + '|'.join('(?:' + scan(p) + ')' for p in patterns) + ')'


def whole(*required, exclude=()):
    return (r'(?i)\A' + ''.join('(?=(?:' + scan(p) + '))' for p in required)
            + ''.join('(?!(?:' + scan(p) + '))' for p in exclude) + r'[\s\S]+\Z')


def token(pattern):
    return r'(?:^|[^A-Za-z0-9])(?:' + pattern + r')(?![A-Za-z0-9])'


def audio_token(pattern):
    return r'(?:^|[^A-Za-z0-9])(?:' + pattern + r')(?=$|[^A-Za-z0-9]|[12567][.]\d)'


def ordered(raw):
    return {s: whole(p, exclude=tuple(list(raw.values())[:i]))
            for i, (s, p) in enumerate(raw.items())}


LOWER_RESOLUTION = token(r'1080[pi]?|fhd|720[pi]?|576[pi]?|480[pi]?')
RESOLUTION_RAW = {
    '4k': either(token(r'4k|2160[pi]?|(?:3840|4096)\s*[x×*]\s*\d{3,4}'), '超高清',
        whole(token(r'uhd|ultra[\s._-]*hd'), exclude=(LOWER_RESOLUTION,))),
    '1080p': token(r'1080[pi]?|fhd|full[\s._-]*hd|1920\s*[x×*]\s*\d{3,4}'),
    '720p': token(r'720[pi]?|1280\s*[x×*]\s*720'),
    '576p': token(r'576[pi]?|720\s*[x×*]\s*576'),
    '480p': token(r'480[pi]?|(?:720|640)\s*[x×*]\s*480'),
}
RESOLUTIONS = ordered(RESOLUTION_RAW)
DV = either(token(r'dolby[\s._-]*vision|dolbyvision|dovi|dv(?:[578])?|dvhe(?:\.\d+(?:\.\d+)?)?|dvh1(?:\.\d+(?:\.\d+)?)?'), r'杜比视界|\u2063')
REMUX = OLD['remux']['pattern']
DISC = token(r'blu[\s._-]*ray|bluray|bdrip|brrip|bdmv|bd25|bd50|bd66|bd100|bdmux|bdremux')
UHD = either(OLD['uhd-bluray']['pattern'], whole(RESOLUTIONS['4k'], DISC,
    exclude=(token(r'1080[pi]?|720[pi]?|576[pi]?|480[pi]?'),)))
SOURCE_RAW = {
    'uhd-remux': whole(REMUX, UHD),
    'remux': REMUX,
    'uhd-bluray': UHD,
    'bluray': DISC,
    'web-dl': OLD['web-dl']['pattern'],
    'webrip': OLD['webrip']['pattern'],
    'hdtv': OLD['hdtv']['pattern'],
    'dvdrip': OLD['dvdrip']['pattern'],
}
SOURCES = ordered(SOURCE_RAW)
SOURCE_LABELS = {
    'uhd-remux': ('UHD REMUX', 'BLU-RAY · REMUX', 'disc', 'gold'),
    'remux': ('REMUX', 'MASTER', 'film', 'gold'),
    'uhd-bluray': ('UHD BLU-RAY', '4K DISC SOURCE', 'disc', 'gold'),
    'bluray': ('BLU-RAY', 'DISC SOURCE', 'disc', 'purple'),
    'web-dl': ('WEB-DL', 'WEB SOURCE', 'web', 'purple'),
    'webrip': ('WEBRip', 'WEB SOURCE', 'web', 'blue'),
    'hdtv': ('HDTV', 'TV SOURCE', 'tv', 'blue'),
    'dvdrip': ('DVDRip', 'DVD SOURCE', 'disc', 'blue'),
}

# DTS/dca/profile compatibility follows the deployed, repaired all9.
# Underlying DD+/DD may now be included in a source badge even when an Atmos
# presentation badge is also present. They are different facts, not substitutes.
def dca_profile(pattern):
    return whole(token('dca'), r'(?:profile|codec[\s._-]*profile|audio[\s._-]*profile)[\s:=._-]*(?:' + pattern + r')(?![A-Za-z0-9])')


DTS_X = either(audio_token(r'dts[:\s._-]*x|dtsx|dca[\s._-]*(?:x|dtsx)'), dca_profile(r'dts[:\s._-]*x|x'))
DTS_HRA = either(audio_token(r'dts[\s._-]*(?:hd[\s._-]*)?hra|dtshd[\s._-]*hra|high[\s._-]*resolution[\s._-]*audio|dts[\s._-]*hd[\s._-]*high[\s._-]*resolution|dca[\s._-]*(?:hra|hdhra)'),
    dca_profile(r'hra|high[\s._-]*resolution(?:[\s._-]*audio)?'))
DTS_MA_EXPLICIT = either(audio_token(r'dts[\s._-]*hd[\s._-]*(?:ma|master(?:[\s._-]*audio)?)|dtshd[\s._-]*ma|dts[\s._-]*ma|dtsma|dts[\s._-]*xll|xll|dca[\s._-]*(?:ma|xll|hdma)'),
    dca_profile(r'ma|dts[\s._-]*hd[\s._-]*ma|master[\s._-]*audio|xll'))
DTS_CORE = audio_token(r'dts|dca(?:[\s._-]*(?:core|coherent[\s._-]*acoustics))?')
DTS_MA = whole(either(DTS_MA_EXPLICIT, whole(DTS_CORE, RESOLUTIONS['4k'], either(DV, REMUX, UHD))), exclude=(DTS_X, DTS_HRA))
DTS_HD = whole(either(DTS_HRA, audio_token(r'dts[\s._-]*hd|dtshd')), exclude=(DTS_X, DTS_MA_EXPLICIT))
AUDIO_RAW = {s: OLD[s]['pattern'] for s in ['truehd', 'dtsx', 'dtshd', 'dtshd-core', 'pcm', 'flac']}
AUDIO_RAW.update({'dtsx': DTS_X, 'dtshd': DTS_MA, 'dtshd-core': DTS_HD})
AUDIO_RAW.update({
    'ddplus': audio_token(r'dolby[\s._-]*digital[\s._-]*plus|e[\s._-]*ac[\s._-]*3|ec[\s._-]*3|ddp|dd\+'),
    'dts': DTS_CORE,
    'dd': audio_token(r'ac[\s._-]*3|dolby[\s._-]*digital(?![\s._-]*(?:plus|\+))|dd(?![\s._-]*(?:plus|\+))'),
    'opus': OLD['opus']['pattern'],
    'aac': audio_token(r'aac(?:[\s._-]*(?:latm|lc|he))?|mp4a'),
    'mp3': OLD['mp3']['pattern'],
})
# A decoder's sample format (e.g. fltp) also occurs with AAC/DD+. Use that
# inherited PCM fallback only when no encoded audio format was supplied.
PCM_EXPLICIT = either(token(r'l?pcm|linear[\s._-]*pcm|raw[\s._-]*pcm|pcm[_-](?:s|u|f)\d+(?:le|be)?|pcm[_-]*(?:bluray|dvd|alaw|mulaw|s24daud|lxf|vidc)|sowt|twos|in24|in32|fl32|fl64'),
    r'(?:^|[^A-Za-z0-9])a[_-]?pcm(?:[/._-]*(?:int|float|ieee|lit|big))*(?![A-Za-z0-9])')
AUDIO_RAW['pcm'] = either(PCM_EXPLICIT, whole(OLD['pcm']['pattern'],
    exclude=tuple(p for s, p in AUDIO_RAW.items() if s != 'pcm')))
AUDIO = ordered(AUDIO_RAW)
AUDIO_LABELS = {'truehd': 'TRUEHD', 'dtsx': 'DTS:X', 'dtshd': 'DTS-HD MA',
    'dtshd-core': 'DTS-HD', 'pcm': 'PCM / LPCM', 'flac': 'FLAC',
    'ddplus': 'DD+', 'dts': 'DTS', 'dd': 'DD / AC-3', 'opus': 'OPUS', 'aac': 'AAC', 'mp3': 'MP3'}
DISC_AUDIO = ['truehd', 'dtsx', 'dtshd', 'dtshd-core', 'pcm', 'ddplus', 'dts', 'dd']
WEB_AUDIO = ['ddplus', 'dd', 'pcm', 'flac', 'opus', 'aac']
SOURCE_AUDIO = {
    'uhd-remux': DISC_AUDIO,
    'remux': DISC_AUDIO,
    'uhd-bluray': DISC_AUDIO,
    'bluray': DISC_AUDIO + ['flac', 'aac'],
    'web-dl': WEB_AUDIO,
    'webrip': WEB_AUDIO,
    'hdtv': ['ddplus', 'dts', 'dd', 'aac', 'mp3'],
    'dvdrip': ['dts', 'dd', 'aac', 'mp3'],
}

# HEVC's playback fallback is retained; explicit other codecs block that
# fallback in the fixture. HEVC/H.265 and AVC/H.264 are aliases, not two badges.
CODEC_RAW = {
    'av1': token(r'av1|av01'),
    'hevc': token(r'hevc|h[\s._-]*265|x265|hvc1|hev1|mpeg[\s._-]*h[\s._-]*part[\s._-]*2'),
    'vp9': token(r'vp9|vp09'),
    'avc': token(r'avc|h[\s._-]*264|x264|avc1|mpeg[\s._-]*4[\s._-]*(?:avc|part[\s._-]*10)'),
    'vc1': token(r'vc[\s._-]*1|wmv3'),
    'mpeg2': token(r'mpeg[\s._-]*2(?:video)?'),
    'divx': token('divx'), 'xvid': token('xvid'),
}
# Keep the all9 HEVC fallback, but bound DV so DVDRip is not Dolby Vision,
# and let explicit legacy codecs block inference just like AV1/VP9/AVC.
CODEC_RAW['hevc'] = either(CODEC_RAW['hevc'], whole(either(
    token(r'main[\s._-]*10'), DV, UHD, whole(RESOLUTIONS['4k'], REMUX)),
    exclude=tuple(p for s, p in CODEC_RAW.items() if s != 'hevc')))
CODECS = ordered(CODEC_RAW)
DEPTH_RAW = {
    '10bit': either(OLD['10bit']['pattern'], token(r'10[\s._-]*bits?|p010(?:le|be)?|yuv\d+p10(?:le|be)?'),
        r'(?:video[\s._-]*bit[\s._-]*depth|视频位深)[\s:="\x27]*10(?!\d)'),
    '8bit': either(token(r'8[\s._-]*bits?|8b|yuv(?:420|422|444)p(?:le|be)?'),
        r'(?:video[\s._-]*bit[\s._-]*depth|视频位深)[\s:="\x27]*8(?!\d)'),
}
DEPTHS = ordered(DEPTH_RAW)
CODEC_LABELS = {'hevc': ('HEVC · H.265', 'purple'), 'avc': ('AVC · H.264', 'blue'),
    'av1': ('AV1', 'gold'), 'vp9': ('VP9', 'purple'), 'vc1': ('VC-1', 'blue'),
    'mpeg2': ('MPEG-2', 'blue'), 'divx': ('DivX', 'blue'), 'xvid': ('XviD', 'blue')}
CODEC_DEPTHS = {s: ['10bit', '8bit'] if s in ['hevc', 'avc', 'av1', 'vp9'] else ['8bit'] for s in CODECS}

# Scope language names to audio evidence. Subtitle names and undetermined
# languages must not create a "bilingual audio" claim.
LANG_DATA = [
    ('chinese', '中', r'chi|zho|zh(?:[-_]cn)?|chinese|mandarin', '中文|国语|普通话'),
    ('english', '英', r'eng|en|english', '英文|英语'),
    ('japanese', '日', r'jpn|ja|japanese', '日文|日语'),
    ('korean', '韩', r'kor|ko|korean', '韩文|韩语'),
]
LANG = {}
AUDIO_PREFIX = r'(?:audio(?:[\s._-]*(?:language|languages|track|tracks))?|音轨(?:语言)?|配音)'
LIST_GAP = r'[\s:：=\[\]"\x27,，;/+&、.()_-]*'
ALL_LANG_NAMES = '(?:' + '|'.join(x[2] + '|' + x[3] for x in LANG_DATA) + ')'
for slug, short, codes, names in LANG_DATA:
    term = f'(?:{codes}|{names})'
    # Only language tokens and separators may occur inside a language list;
    # "Audio: eng; subtitles: jpn" cannot leak the subtitle into audio.
    prefix = AUDIO_PREFIX + LIST_GAP + '(?:' + ALL_LANG_NAMES + LIST_GAP + '){0,7}' + term + r'(?![A-Za-z])'
    suffix = term + r'[\s._-]*(?:audio|track|音轨|配音)(?![A-Za-z])'
    standalone = r'\A\s*(?:' + codes + '|' + names + r')\s*\Z'
    short_label = r'[中英日韩]{0,3}' + short + r'[中英日韩]{0,3}(?:双语)?(?:音轨|配音)'
    LANG[slug] = either(prefix, suffix, standalone, short_label)

ATMOS_EXPLICIT = either(audio_token(r'dolby[\s._-]*atmos|atmos|joc'), r'杜比全景声|全景声')
DV_ATMOS = whole(DV, either(OLD['combo-dv-atmos']['pattern'], ATMOS_EXPLICIT))


def channel_rules():
    # The original native matcher covers codec-adjacent DDP5.1/AAC2.0 and
    # excludes codec Level/Profile 5.1. Retain all9's mono/stereo count aliases.
    from badge_rules import P
    raw = {s: P[s] for s in ['71', '61', '51']}
    for s, count, alias in [('20', 2, 'stereo'), ('10', 1, 'mono')]:
        raw[s] = either(P[s], token(alias + r'(?:[\s._-]*audio)?'),
            token(str(count) + r'[\s._-]*(?:ch|channels?)'),
            r'(?:audio[\s._-]*channels?|channels?|channel[\s._-]*count|声道)[\s:=_-]*' + str(count) + r'\b')
    return ordered(raw)

GROUPS = [
    ('resolution', '分辨率'), ('source-audio', '片源与音频'),
    ('video-tech', '杜比与画面'), ('audio-tech', '音频格式'),
    ('edition', '版本标识'), ('platform', '平台来源'),
    ('video-codec', '编码与位深'), ('audio-channels', '声道'),
    ('audio-language', '音轨语言'),
]


def make_filter(slug, name, group, pattern, image=None):
    return dict(id='ly10-' + slug, name=name, groupId=group, pattern=pattern,
        imageURL=image or f'{BASE}/png/{slug}.png', tagColor='#00000000',
        borderColor='#00000000', textColor='#00000000', tagStyle='filled',
        isEnabled=True, type='filter')


def build():
    filters, new_assets = [], []

    def keep(slug, group=None, pattern=None, name=None, image=None):
        f = copy.deepcopy(OLD[slug])
        f.update(id='ly10-' + slug)
        if group is not None: f['groupId'] = group
        if pattern is not None: f['pattern'] = pattern
        if name is not None: f['name'] = name
        if image is not None: f['imageURL'] = image
        filters.append(f)

    def add(slug, title, subtitle, group, pattern, icon, color, **facts):
        filters.append(make_filter(slug, title + ' · ' + subtitle, group, pattern))
        new_assets.append(dict(slug=slug, title=title, subtitle=subtitle,
            category=group, icon=icon, color=color, **facts))

    # Keep 4K literally first in both array order and group order.
    for s in ['4k', '1080p', '720p', '576p', '480p']:
        keep(s, 'resolution', RESOLUTIONS[s])

    for source, allowed in SOURCE_AUDIO.items():
        title, subtitle, icon, color = SOURCE_LABELS[source]
        for audio in allowed:
            label = AUDIO_LABELS[audio] + (' · 蓝光' if source == 'uhd-remux' else '')
            add(f'combo-{source}-{audio}', title, label, 'source-audio',
                whole(SOURCES[source], AUDIO[audio]), icon, color,
                family='source-audio', source=source, audio=audio)
        fallback = whole(SOURCES[source], exclude=(either(*(AUDIO[a] for a in allowed)),))
        if source == 'uhd-remux':
            add(source, title, subtitle, 'source-audio', fallback, icon, color,
                family='source', source=source)
        else:
            keep(source, 'source-audio', fallback)

    keep('combo-dv-atmos', 'video-tech', '(?i)' + bare(DV_ATMOS))
    keep('dolby-vision', 'video-tech', whole(DV, exclude=(DV_ATMOS,)))
    for s in ['hdr10plus', 'hdr10', 'hlg', 'hdr',
              'sdr', 'imax-enhanced', 'imax', '3d']:
        keep(s, 'video-tech')
    keep('atmos', 'audio-tech', whole(either(OLD['atmos']['pattern'], ATMOS_EXPLICIT), exclude=(DV_ATMOS,)))
    for audio in AUDIO:
        combined_sources = [SOURCES[s] for s, allowed in SOURCE_AUDIO.items() if audio in allowed]
        exclusions = (either(*combined_sources),) if combined_sources else ()
        keep(audio, 'audio-tech', whole(AUDIO[audio], exclude=exclusions))

    for s in ['directors-cut', 'extended', 'remastered', 'open-matte', 'repack',
              'proper', 'criterion', 'hybrid', 'black-white', 'theatrical']:
        keep(s, 'edition')
    for s in ['netflix', 'prime-video', 'apple-tv', 'disney-plus', 'max', 'hulu',
              'peacock', 'paramount-plus', 'crunchyroll']:
        keep(s, 'platform')

    for codec, depths in CODEC_DEPTHS.items():
        title, color = CODEC_LABELS[codec]
        for depth in depths:
            subtitle = depth.removesuffix('bit') + ' BIT'
            add(f'combo-{codec}-{depth}', title, subtitle, 'video-codec',
                whole(CODECS[codec], DEPTHS[depth]), 'chip', color,
                family='codec-depth', codec=codec, depth=depth)
        fallback = whole(CODECS[codec], exclude=(either(*(DEPTHS[d] for d in depths)),))
        if codec in ['hevc', 'avc']:
            add(codec, title, 'VIDEO CODEC', 'video-codec', fallback, 'chip', color,
                family='codec', codec=codec)
        else:
            keep(codec, 'video-codec', fallback)
    for depth in DEPTHS:
        combining = [CODECS[c] for c, ds in CODEC_DEPTHS.items() if depth in ds]
        keep(depth, 'video-codec', whole(DEPTHS[depth], exclude=(either(*combining),)))
    # FPS is technical information, after the codec/depth badge.
    frame_raw = {s: OLD[s]['pattern'] for s in ['120fps', '60fps', '50fps']}
    for s, p in ordered(frame_raw).items(): keep(s, 'video-codec', p)
    for s, p in channel_rules().items(): keep(s, 'audio-channels', p)

    languages = list(LANG)
    shorts = {s: short for s, short, _, _ in LANG_DATA}
    codes = {'chinese': 'ZH', 'english': 'EN', 'japanese': 'JA', 'korean': 'KO'}
    # Exact set membership gives one 2/3/4-language badge, never all pairs.
    for count in [4, 3, 2]:
        for subset in itertools.combinations(languages, count):
            add('audio-' + '-'.join(subset), ''.join(shorts[s] for s in subset) + '音轨',
                ' + '.join(codes[s] for s in subset), 'audio-language',
                whole(*(LANG[s] for s in subset), exclude=tuple(LANG[s] for s in languages if s not in subset)),
                'language', 'blue', family='language', languages=list(subset))
    for s in languages:
        keep(s, 'audio-language', whole(LANG[s], exclude=tuple(LANG[t] for t in languages if t != s)))

    config = dict(filters=filters, groups=[dict(id=s, name=n, color='#00000000',
        borderColor='#00000000', isExpanded=True) for s, n in GROUPS])
    return config, new_assets


def write_configs():
    from portable_badges import write_configs as write_current, ASSETS as assets
    return write_current()['all'], assets


def render_assets(font):
    import render_badges as render
    render.set_font(font)
    _, assets = build()
    for b in assets:
        svg = ASSETS / 'svg' / (b['slug'] + '.svg')
        png = ASSETS / 'png' / (b['slug'] + '.png')
        svg.parent.mkdir(parents=True, exist_ok=True)
        content = render.make_svg(b, 'all')
        if not svg.exists() or svg.read_text() != content: svg.write_text(content)
        render.render_png((svg, png))
    return assets


def matches(text, config=None):
    import re
    config = config or build()[0]
    return [f for f in config['filters'] if re.search(f['pattern'], text)]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render', action='store_true')
    parser.add_argument('--font')
    args = parser.parse_args()
    config, assets = write_configs()
    if args.render: render_assets(args.font)
    print(json.dumps(dict(filters=len(config['filters']), new_assets=len(assets), configs=CONFIGS)))
