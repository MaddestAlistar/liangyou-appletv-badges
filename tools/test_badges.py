"""Behavior tests for single-input rules; also demonstrates candidate-union limits."""
import base64, ctypes, ctypes.util, itertools, json, re, subprocess, time
from pathlib import Path
import badge_rules as r

ROOT=r.ROOT
CASES=[]
def case(text,epx,all_=None):
    for version,expected in [('epx',epx),('all',epx if all_ is None else all_)]:
        CASES.append(dict(version=version,text=text,expected=sorted(expected.split() if isinstance(expected,str) else expected)))

case('Movie.2160p.UHD.BluRay.REMUX.DV.TrueHD.Atmos.7.1.HEVC','4k remux combo-dv-atmos-truehd 71 hevc')
case('Dolby Vision\nE-AC-3 JOC\n5.1','combo-dv-atmos-ddplus 51')
case('Atmos\r\nDV\r\nTrueHD','combo-dv-atmos-truehd')
case('Dolby Vision\nAtmos','combo-dv-atmos')
case('DoVi True HD','combo-dv-truehd')
case('TrueHD Atmos','combo-atmos-truehd')
case('EAC3 JOC','combo-atmos-ddplus')
case('DTS:X DTS-HD MA 7.1','combo-dtsx-dtshd 71')
case('DV Atmos TrueHD EAC3','combo-dv-atmos-truehd ddplus')
case('DV Atmos DTS:X DTS-HD MA','combo-dv-atmos combo-dtsx-dtshd')
for alias in ['HDR10+','HDR10Plus','HDR10P','HDR 10 +','hdr10+','file_HDR10+_end','HDR10+\nHDR10','\u2064']:
    case(alias,'hdr10plus')
case('HDR10','hdr10');case('HDR','hdr');case('HLG','hlg');case('Hybrid Log Gamma','hlg')
case('SDR','sdr');case('DV HDR10','dolby-vision hdr10');case('Dolby Vision HDR10+','dolby-vision hdr10plus')
case('DV SDR','dolby-vision');case('HDTV','hdtv');case('WEBRip','webrip');case('WEB-DL','web-dl')
case('WEBRip WEB-DL','webrip');case('NF WEBRip','webrip','webrip netflix')
case('NF','');case('Mad.Max.2015.1080p','1080p');case('HMAX WEB-DL','web-dl','web-dl max')
case('Movie.1080p.UHD.BluRay','1080p bluray');case('Movie_4K_UHD_BluRay','4k uhd-bluray')
case('Movie.3840x1600.REMUX','4k remux');case('1920×1080','1080p');case('2160p 1080p','4k')
case('576p DVDRip','','576p dvdrip');case('480p','','480p')
case('HD','');case('CAM','');case('DVD','');case('UHD','4k')
for alias in ['HEVC','H.265','H265','x265','hvc1','hev1']:case(alias,'hevc')
for alias in ['AVC','H.264','x264','avc1','MPEG-4 AVC']:case(alias,'avc')
case('MPEG4','');case('MPEG-4','');case('Main10','');case('AV1 Main10','av1')
case('VP9 Profile 2','vp9');case('XviD MPEG4','','xvid');case('MPEG-2 VC-1','','mpeg2 vc1')
case('10-bit HEVC','10bit hevc');case('8bit AVC','8bit avc');case('yuv420p10le','10bit')
case('p010le','10bit');case('Video BitDepth=10','10bit');case('Audio BitDepth=24','')
for alias in ['EAC3','E-AC-3','DD+','DDP','Dolby Digital Plus']:case(alias,'ddplus')
for alias in ['AC3','AC-3','DD','Dolby Digital']:case(alias,'dd')
case('EAC35.1','ddplus 51');case('DDP5.1','ddplus 51');case('DD+5.1','ddplus 51');case('TrueHD5.1','truehd 51')
case('AC35.1','dd 51');case('AAC2.0','aac 20');case('DTS-HD.MA5.1','dtshd 51')
case('DTS','dts');case('DTS-HD','dtshd-core');case('DTS-HD HRA','dtshd-core');case('DTS-HD MA','dtshd')
case('DTS XLL','dtshd');case('DTS:X','dtsx');case('PCM_S24LE','pcm');case('LPCM','pcm');case('MP3','','mp3')
case('5.1','51');case('7.1','71');case('6.1','61');case('2.0','20');case('1.0','10')
case('Mono','10');case('Stereo','20');case('Audio: Mono','10');case('Stereo Audio','20')
case('L5.1','');case('Level 5.1','');case('Level: 5.1','');case('Profile 5.1','')
case('HEVC Level 5.1 AAC 2.0','hevc aac 20');case('Level 5.1 AAC 5.1','aac 51')
case('Version 2.0','');case('6ch','');case('8 channels','')
case('IMAX Enhanced','imax-enhanced');case('IMAX','imax')
case('3D SBS','','3d');case('60 fps','','60fps');case('120FPS','','120fps');case('50 fps','','50fps')
case('FrameRate=60','','60fps');case('120 Mbps','');case('Audio 48000 Hz','')
case('Hybrid Log Gamma','hlg');case('Hybrid WEB-DL','web-dl','hybrid web-dl')
case('中文字幕','');case('English subtitles','');case('Audio: eng','','english');case('Audio Language: jpn','','japanese')
case('中文音轨','','chinese');case('国语配音','','chinese');case('韩语音轨','','korean')
case('English Audio','','english');case('Netflix WEB-DL','web-dl','netflix web-dl')
case('ATVP WEB-DL','web-dl','apple-tv web-dl');case('DSNP WEB-DL','web-dl','disney-plus web-dl')
case('Hulu WEB-DL','web-dl','hulu web-dl');case('PCOK WEBRip','webrip','peacock webrip')
case('PMTP WEB-DL','web-dl','paramount-plus web-dl');case('AMZN WEB-DL','web-dl','prime-video web-dl')
case('Crunchyroll WEBRip','webrip','crunchyroll webrip')
for label,slug in [("Director's Cut",'directors-cut'),('EXTENDED','extended'),('Remastered','remastered'),('Open Matte','open-matte'),('Repack','repack'),('Proper','proper'),('Criterion','criterion'),('Black & White','black-white'),('Theatrical Cut','theatrical')]:case(label,'',slug)
for p in [5,7,8]:
    for s in [f'Dolby Vision Profile {p}',f'DV P{p}',f'dvhe.0{p}.06',f'DV{p}']:
        case(s,'dolby-vision',f'dv-p{p}')
        case(s+' TrueHD Atmos','combo-dv-atmos-truehd',f'combo-dv-atmos-truehd-p{p}')
        case(s+' EAC3 Atmos','combo-dv-atmos-ddplus',f'combo-dv-atmos-ddplus-p{p}')
        case(s+' Atmos','combo-dv-atmos',f'combo-dv-atmos-p{p}')
        case(s+' TrueHD','combo-dv-truehd',f'combo-dv-truehd-p{p}')
case('Profile 5','');case('DV P5 DV P7 Atmos','combo-dv-atmos');case('DV P5 DV P7','dolby-vision')
case('\u2063 \u2064','dolby-vision hdr10plus');case('Title_DolbyVision_Atmos_TrueHD','combo-dv-atmos-truehd')
for pieces in itertools.permutations(['DV','Atmos','TrueHD']):
    for sep in [' ', '\n', '\r\n', '_']:
        case(sep.join(pieces),'combo-dv-atmos-truehd')

class ICU:
    """ICU regex uses the same syntax family as NSRegularExpression, not an iOS UI test."""
    def __init__(self):
        path=ctypes.util.find_library('icui18n');self.lib=ctypes.CDLL(path)
        suffix=re.search(r'\.so\.(\d+)',path).group(1)
        def fn(name,args,ret):
            f=getattr(self.lib,name+'_'+suffix);f.argtypes=args;f.restype=ret;return f
        self.open=fn('uregex_open',[ctypes.POINTER(ctypes.c_uint16),ctypes.c_int32,ctypes.c_uint32,ctypes.c_void_p,ctypes.POINTER(ctypes.c_int32)],ctypes.c_void_p)
        self.set=fn('uregex_setText',[ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint16),ctypes.c_int32,ctypes.POINTER(ctypes.c_int32)],None)
        self.find=fn('uregex_find',[ctypes.c_void_p,ctypes.c_int32,ctypes.POINTER(ctypes.c_int32)],ctypes.c_int8)
        self.close=fn('uregex_close',[ctypes.c_void_p],None)
        self.limit=fn('uregex_setTimeLimit',[ctypes.c_void_p,ctypes.c_int32,ctypes.POINTER(ctypes.c_int32)],None)
        self.cache={}
    def u16(self,text):
        b=text.encode('utf-16-le');n=len(b)//2
        return (ctypes.c_uint16*max(n,1)).from_buffer_copy(b or b'\0\0'),n
    def matches(self,pattern,text):
        e=ctypes.c_int32(0)
        if pattern not in self.cache:
            buf,n=self.u16(pattern);handle=self.open(buf,n,0,None,ctypes.byref(e))
            if e.value>0:raise AssertionError(('ICU compile',e.value,pattern))
            self.limit(handle,1000,ctypes.byref(e));self.cache[pattern]=handle
        handle=self.cache[pattern];buf,n=self.u16(text);self.set(handle,buf,n,ctypes.byref(e));hit=bool(self.find(handle,0,ctypes.byref(e)))
        if e.value>0:raise AssertionError(('ICU match',e.value,text[:120],len(text)))
        return hit

def run():
    rules={v:r.make_config(v)['filters'] for v in ['epx','all']}
    icu=ICU();fails=[];start=time.monotonic()
    for v,fs in rules.items():
        assert len({f['id'] for f in fs})==len(fs),'duplicate id'
        assert len({f['imageURL'] for f in fs})==len(fs),'duplicate image'
        assert all(f['groupId'] in {i for i,_ in r.GROUPS} for f in fs)
    for c in CASES:
        expected=c['expected']
        for engine,matcher in [('Python',lambda p,t:bool(re.search(p,t))),('ICU',icu.matches)]:
            found=sorted(f['id'][4:] for f in rules[c['version']] if matcher(f['pattern'],c['text']))
            if found!=expected:fails.append(dict(engine=engine,case=c,actual=found))
    if fails:
        print(json.dumps({'failed':len(fails),'examples':fails[:18]},ensure_ascii=False,indent=2));raise SystemExit(1)
    report=ROOT/'reports';report.mkdir(exist_ok=True)
    enc=lambda s:base64.b64encode(s.encode()).decode()
    (report/'regex-rules.tsv').write_text('\n'.join(v+'\t'+f['id'][4:]+'\t'+enc(f['pattern']) for v,fs in rules.items() for f in fs)+'\n')
    (report/'regex-cases.tsv').write_text('\n'.join(c['version']+'\t'+enc(c['text'])+'\t'+(','.join(c['expected']) or '-') for c in CASES)+'\n')
    java=subprocess.run(['java',str(ROOT/'tools/RegexCheck.java'),str(report)],capture_output=True,text=True)
    if java.returncode:raise RuntimeError(java.stdout+java.stderr)
    # Reproduce the official NuvioTV candidate union algorithm. This limitation must stay visible.
    candidates=['DV','Atmos','TrueHD','DV Atmos TrueHD']
    union=sorted(f['id'][4:] for f in rules['epx'] if any(re.search(f['pattern'],c) for c in candidates))
    assert union==['atmos','combo-dv-atmos-truehd','dolby-vision','truehd']
    start_perf=time.monotonic()
    noise='x'*10000
    for fs in rules.values():
        for f in fs:icu.matches(f['pattern'],noise)
    perf=time.monotonic()-start_perf
    result=dict(configs={v:len(fs) for v,fs in rules.items()},cases=len(CASES),engines=['Python re','ICU 74','Java 17 Pattern'],assertions=len(CASES)*3,passed=True,elapsed_seconds=round(time.monotonic()-start,3),noise_10000_char_seconds=round(perf,3),candidate_union_limitation={'input_fields':candidates[:-1],'result':union,'global_exclusion_possible_in_this_matcher':False},device_tested=False)
    (report/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':run()
