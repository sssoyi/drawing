#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""도안 나눔 공유페이지 생성기.

사용법:  python3 만들기.py     (또는 '페이지만들기.command' 더블클릭)

- 도안이미지/ 폴더에 있는 그림을 한 장씩 A4 페이지로 만들어 넣습니다.
- 옆에 있는 .MP4 영상을 '영상 보기' 칸에 넣습니다. (포스터/ 폴더의 같은 이름 jpg를 썸네일로 사용)
- 결과물: 공유페이지.html  (이미지가 파일 안에 들어있어서 이 파일 하나만 보내도 그림은 다 보입니다.
  영상까지 보이게 하려면 drawing 폴더를 통째로 공유하세요.)
"""

import base64
import html
import os
import re
import shutil
import subprocess
import tempfile
import unicodedata
from urllib.parse import quote

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(HERE, "도안이미지")
VIDEO_DIR = os.path.join(HERE, "영상")
POSTER_DIR = os.path.join(HERE, "포스터")
OUT = os.path.join(HERE, "index.html")  # 웹에 올리려면 이름이 index.html 이어야 함

PAGE_TITLE = "엄마표 그림 도안 나눔"
PAGE_SUB = "공룡 · 바다동물 · 중장비 · 긴급차량 · 도형<br>영상 보고 따라 그려보세요. 도안은 A4로 출력하면 딱 맞아요."
CREDIT = "@luckyyy.mommy"

IMG_EXT = (".png", ".jpg", ".jpeg", ".webp", ".heic", ".heif", ".gif")
MAX_PX = 1800  # 긴 변 기준 리사이즈 (A4 출력에 충분)

# 영상 노출 순서와 제목. (파일명 → 화면에 보일 제목)
# 영상을 추가하면 여기에 한 줄만 넣으면 됩니다. 없으면 파일명이 그대로 제목이 돼요.
VIDEO_LABEL = {
    "dino-1": "공룡 그리기 1탄",
    "dino-2": "공룡 그리기 2탄",
    "sea": "바다동물 그리기",
    "machine": "중장비 그리기",
    "emergency": "경찰차 · 구급차 · 소방차",
    "shapes": "도형으로 그리기",
    # 원본 한글 파일명을 쓸 때를 위한 대비
    "공룡1": "공룡 그리기 1탄", "공룡2": "공룡 그리기 2탄",
    "바다동물": "바다동물 그리기", "중장비": "중장비 그리기",
    "경찰차소방차": "경찰차 · 구급차 · 소방차", "도형": "도형으로 그리기",
}
VIDEO_ORDER = ["dino-1", "dino-2", "sea", "machine", "emergency", "shapes",
               "공룡1", "공룡2", "바다동물", "중장비", "경찰차소방차", "도형"]


def nfc(s):
    """맥은 파일명을 자모 분리(NFD)로 돌려줘서, 비교/표시 전에 합쳐준다."""
    return unicodedata.normalize("NFC", s)


def natural_key(name):
    return [int(t) if t.isdigit() else t.lower()
            for t in re.split(r"(\d+)", nfc(name))]


def pretty_title(filename):
    stem = nfc(os.path.splitext(filename)[0])
    stem = re.sub(r"^\s*\d+\s*[-_.)]\s*", "", stem)  # "01-공룡" -> "공룡"
    return stem.strip() or os.path.splitext(filename)[0]


def data_uri(path):
    ext = os.path.splitext(path)[1].lower()
    mime = {
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".webp": "image/webp", ".gif": "image/gif",
    }.get(ext, "image/jpeg")
    with open(path, "rb") as f:
        return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode("ascii"))


def web_copy(src, workdir):
    """sips로 리사이즈(+HEIC는 jpeg 변환)한 사본 경로를 돌려준다."""
    ext = os.path.splitext(src)[1].lower()
    base = os.path.splitext(os.path.basename(src))[0]
    if ext in (".heic", ".heif"):
        dst = os.path.join(workdir, base + ".jpg")
        cmd = ["sips", "-Z", str(MAX_PX), "-s", "format", "jpeg",
               "-s", "formatOptions", "82", src, "--out", dst]
    elif ext == ".gif":
        return src
    else:
        dst = os.path.join(workdir, base + ext)
        cmd = ["sips", "-Z", str(MAX_PX), src, "--out", dst]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        if os.path.getsize(dst) > 0:
            return dst
    except Exception:
        pass
    return src


def download_name(filename):
    stem = pretty_title(filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext in (".heic", ".heif"):
        ext = ".jpg"
    return stem + ext


# ---------------------------------------------------------------- 수집
os.makedirs(IMG_DIR, exist_ok=True)

files = sorted(
    [f for f in os.listdir(IMG_DIR)
     if f.lower().endswith(IMG_EXT) and not f.startswith(".")],
    key=natural_key,
)

sheets, dl_items = [], []
workdir = tempfile.mkdtemp()
try:
    for i, f in enumerate(files):
        src = os.path.join(IMG_DIR, f)
        uri = data_uri(web_copy(src, workdir))
        title = html.escape(pretty_title(f))
        dname = html.escape(download_name(f))
        sheets.append("""      <figure class="item">
        <div class="sheet"><img src="{uri}" alt="{title}"></div>
        <figcaption>
          <span class="cap-name">{title}</span>
          <a class="btn-ghost" href="{uri}" download="{dname}">받기</a>
        </figcaption>
      </figure>""".format(uri=uri, title=title, dname=dname))
        dl_items.append('{n:"%s",i:%d}' % (dname.replace('"', ""), i))
finally:
    shutil.rmtree(workdir, ignore_errors=True)

# 영상: H.264로 변환해둔 영상/ 폴더를 우선 사용 (원본 .MP4는 HEVC라 크롬에서 재생 불가)
warn = ""
if os.path.isdir(VIDEO_DIR) and any(f.lower().endswith(".mp4")
                                    for f in os.listdir(VIDEO_DIR)):
    vid_base, prefix = VIDEO_DIR, "영상/"
else:
    vid_base, prefix = HERE, ""
    warn = ("\n※ 영상/ 폴더가 없어 원본 .MP4를 씁니다. 원본은 HEVC(H.265)라\n"
            "  크롬·윈도우·안드로이드에서는 재생이 안 될 수 있어요.")

vids = [f for f in os.listdir(vid_base)
        if f.lower().endswith(".mp4") and not f.startswith(".")]
vids.sort(key=lambda f: (VIDEO_ORDER.index(nfc(os.path.splitext(f)[0]))
                         if nfc(os.path.splitext(f)[0]) in VIDEO_ORDER else 99,
                         natural_key(f)))

cards = []
for f in vids:
    stem = nfc(os.path.splitext(f)[0])
    poster = os.path.join(POSTER_DIR, stem + ".jpg")
    pos = ' poster="%s"' % data_uri(poster) if os.path.exists(poster) else ""
    label = html.escape(VIDEO_LABEL.get(stem, stem))
    cards.append("""      <article class="clip">
        <div class="vwrap">
          <video controls preload="none" playsinline{pos} data-title="{label}">
            <source src="{src}" type="video/mp4">
          </video>
        </div>
        <h3>{label}</h3>
      </article>""".format(pos=pos, src=quote(prefix) + quote(f), label=label))

empty_note = "" if sheets else """      <div class="empty">
        <b>아직 도안 이미지가 없어요.</b>
        <p><code>drawing/도안이미지/</code> 폴더에 그림 파일을 넣고<br>
        <code>페이지만들기.command</code> 를 다시 실행하면 여기에 한 장씩 채워집니다.</p>
        <p class="hint">파일 이름이 그대로 제목이 돼요. 순서를 정하고 싶으면
        <code>01-스테고사우루스.png</code> 처럼 앞에 번호를 붙이세요.</p>
      </div>"""

# ---------------------------------------------------------------- HTML
TPL = r"""<!doctype html>
<html lang="ko">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  :root {
    --ink:#1c1a17; --muted:#8b8478; --line:#e6e1d8;
    --paper:#fffdf9; --bg:#f6f3ee; --accent:#c2624a;
  }
  * { box-sizing:border-box; }
  body {
    margin:0; background:var(--bg); color:var(--ink);
    font-family:'Apple SD Gothic Neo','Pretendard',-apple-system,system-ui,sans-serif;
    line-height:1.6; -webkit-font-smoothing:antialiased;
  }
  .wrap { max-width:1080px; margin:0 auto; padding:0 20px 80px; }

  header { padding:64px 0 40px; text-align:center; }
  header h1 { font-size:32px; font-weight:700; margin:0 0 12px; letter-spacing:-.02em; }
  header p { margin:0 auto; color:var(--muted); font-size:15px; max-width:520px; }
  .tools { margin-top:26px; display:flex; gap:10px; justify-content:center; flex-wrap:wrap; }

  .btn {
    appearance:none; border:0; cursor:pointer; font:inherit; font-size:14px;
    padding:11px 20px; border-radius:999px; background:var(--ink); color:#fff;
    transition:opacity .15s;
  }
  .btn:hover { opacity:.85; }
  .btn[disabled] { opacity:.45; cursor:default; }
  .btn-line {
    background:transparent; color:var(--ink); border:1px solid var(--line);
  }
  .btn-ghost {
    font-size:12.5px; text-decoration:none; color:var(--muted);
    border:1px solid var(--line); border-radius:999px; padding:5px 13px;
    background:var(--paper); transition:.15s; white-space:nowrap;
  }
  .btn-ghost:hover { color:var(--ink); border-color:var(--ink); }

  h2 {
    font-size:14px; font-weight:600; letter-spacing:.02em; margin:0 0 20px;
    padding-bottom:12px; border-bottom:1px solid var(--line); color:var(--muted);
  }
  section { margin-top:56px; }

  .clips { display:grid; grid-template-columns:repeat(3,1fr); gap:22px; }
  .vwrap { position:relative; }
  .clip video {
    width:100%; aspect-ratio:9/16; object-fit:cover; display:block;
    border-radius:14px; background:#111; border:1px solid var(--line);
  }
  .clip h3 { font-size:14px; font-weight:500; margin:10px 2px 0; }

  .grid { display:grid; grid-template-columns:repeat(2,1fr); gap:28px 24px; }
  .item { margin:0; }
  .sheet {
    aspect-ratio:1/1.4142; background:var(--paper); border:1px solid var(--line);
    border-radius:4px; padding:7%; display:flex; align-items:center;
    justify-content:center; box-shadow:0 1px 3px rgba(0,0,0,.05);
  }
  .sheet img { max-width:100%; max-height:100%; object-fit:contain; display:block; }
  figcaption {
    display:flex; align-items:center; justify-content:space-between;
    gap:12px; margin-top:11px; padding:0 2px;
  }
  .cap-name { font-size:14px; }

  .empty {
    border:1px dashed var(--line); border-radius:10px; padding:40px 28px;
    text-align:center; color:var(--muted); background:var(--paper);
  }
  .empty b { color:var(--ink); font-size:15px; }
  .empty p { margin:12px 0 0; font-size:14px; }
  .empty .hint { font-size:13px; opacity:.8; }
  code {
    font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12.5px;
    background:#efeae1; padding:2px 6px; border-radius:4px;
  }

  footer {
    margin-top:72px; padding-top:24px; border-top:1px solid var(--line);
    text-align:center; color:var(--muted); font-size:13px;
  }
  #toast {
    position:fixed; left:50%; bottom:28px; transform:translate(-50%,20px);
    background:var(--ink); color:#fff; font-size:13.5px; padding:11px 20px;
    border-radius:999px; opacity:0; pointer-events:none; transition:.25s;
  }
  #toast.on { opacity:1; transform:translate(-50%,0); }

  /* ---- 영상 크게 보기 (모바일에서 썸네일을 누르면 열림) ---- */
  #viewer {
    position:fixed; inset:0; z-index:50; background:rgba(20,18,16,.94);
    display:flex; align-items:center; justify-content:center; padding:16px;
  }
  #viewer[hidden] { display:none; }
  #viewer video {
    max-width:100%; max-height:100%; width:auto; border-radius:10px;
    background:#000; display:block;
  }
  #viewer-close {
    position:absolute; top:calc(env(safe-area-inset-top, 0px) + 12px); right:14px;
    width:40px; height:40px; border:0; border-radius:50%; cursor:pointer;
    background:rgba(255,255,255,.16); color:#fff; font-size:19px; line-height:1;
    display:flex; align-items:center; justify-content:center;
  }
  #viewer-title {
    position:absolute; top:calc(env(safe-area-inset-top, 0px) + 22px); left:18px;
    color:rgba(255,255,255,.82); font-size:14px; margin:0;
  }

  @media (max-width:860px) {
    .wrap { padding:0 14px 60px; }
    header { padding:36px 0 24px; }
    header h1 { font-size:23px; }
    header p { font-size:13.5px; }
    .btn { padding:10px 17px; font-size:13.5px; }
    section { margin-top:40px; }

    /* 영상: 한 줄에 3개 썸네일 */
    .clips { grid-template-columns:repeat(3,1fr); gap:9px; }
    .clip video { border-radius:9px; pointer-events:none; }
    .clip h3 {
      font-size:11.5px; margin:7px 1px 0; line-height:1.35;
      overflow:hidden; display:-webkit-box; -webkit-line-clamp:2;
      -webkit-box-orient:vertical;
    }
    .vwrap::after {
      content:''; position:absolute; inset:0; margin:auto;
      width:0; height:0; transform:translateX(2px);
      border-left:15px solid rgba(255,255,255,.95);
      border-top:10px solid transparent; border-bottom:10px solid transparent;
      filter:drop-shadow(0 1px 4px rgba(0,0,0,.55));
    }

    /* 도안: 가로 2열 */
    .grid { grid-template-columns:repeat(2,1fr); gap:20px 12px; }
    .sheet { padding:6%; border-radius:3px; }
    figcaption { margin-top:8px; gap:6px; }
    .cap-name {
      font-size:12.5px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
    }
    .btn-ghost { font-size:11.5px; padding:4px 10px; }
  }

  @page { size:A4; margin:0; }
  @media print {
    body { background:#fff; }
    header, .tools, #videos, footer, figcaption, #toast { display:none !important; }
    .wrap { max-width:none; padding:0; }
    section { margin:0; }
    h2 { display:none; }
    .grid { display:block; }
    .item { break-after:page; page-break-after:always; }
    .sheet {
      width:210mm; height:297mm; border:0; border-radius:0; box-shadow:none;
      padding:18mm; background:#fff;
    }
  }
</style>

<div class="wrap">
  <header>
    <h1>__TITLE__</h1>
    <p>__SUB__</p>
    <div class="tools">
      <button class="btn" id="dl-all">도안 전체 받기 (__COUNT__장)</button>
      <button class="btn btn-line" onclick="window.print()">A4로 인쇄하기</button>
    </div>
  </header>

  <section id="videos">
    <h2>영상 보고 따라 그리기</h2>
    <div class="clips">
__CARDS__
    </div>
  </section>

  <section id="sheets">
    <h2>도안 내려받기</h2>
    <div class="grid">
__SHEETS__
    </div>
__EMPTY__
  </section>

  <footer>__CREDIT__</footer>
</div>

<div id="viewer" hidden>
  <p id="viewer-title"></p>
  <button id="viewer-close" aria-label="닫기">✕</button>
  <video controls playsinline preload="auto"></video>
</div>

<div id="toast"></div>

<script>
(function () {
  var toastEl = document.getElementById('toast'), timer;
  function toast(msg) {
    toastEl.textContent = msg; toastEl.classList.add('on');
    clearTimeout(timer); timer = setTimeout(function () {
      toastEl.classList.remove('on');
    }, 2200);
  }

  // ---- 화면 크기에 따라 영상 동작을 바꾼다 ----
  // 넓은 화면: 카드에서 바로 재생 / 좁은 화면: 썸네일을 누르면 크게 열림
  var small = window.matchMedia('(max-width: 860px)');
  var clips = [].slice.call(document.querySelectorAll('.clip video'));

  clips.forEach(function (v) {
    v.addEventListener('play', function () {   // 한 번에 한 영상만
      clips.forEach(function (o) { if (o !== v) o.pause(); });
    });
  });

  function applyMode() {
    clips.forEach(function (v) {
      if (small.matches) { v.pause(); v.removeAttribute('controls'); }
      else { v.setAttribute('controls', ''); }
    });
    if (!small.matches) closeViewer();
  }
  applyMode();
  (small.addEventListener ? small.addEventListener('change', applyMode)
                          : small.addListener(applyMode));

  var viewer = document.getElementById('viewer');
  var vv = viewer.querySelector('video');
  var vtitle = document.getElementById('viewer-title');

  function openViewer(src, title) {
    vv.src = src;
    vtitle.textContent = title || '';
    viewer.hidden = false;
    document.body.style.overflow = 'hidden';
    vv.play().catch(function () {});   // 자동재생이 막히면 재생버튼으로
  }
  function closeViewer() {
    if (viewer.hidden) return;
    vv.pause();
    vv.removeAttribute('src');
    vv.load();
    viewer.hidden = true;
    document.body.style.overflow = '';
  }

  document.querySelectorAll('.clip').forEach(function (clip) {
    clip.addEventListener('click', function () {
      if (!small.matches) return;              // 넓은 화면은 원래대로 인라인 재생
      var v = clip.querySelector('video');
      var s = v.querySelector('source');
      if (s) openViewer(s.getAttribute('src'), v.dataset.title);
    });
  });

  document.getElementById('viewer-close').addEventListener('click', closeViewer);
  viewer.addEventListener('click', function (e) {   // 영상 바깥을 눌러도 닫힘
    if (e.target === viewer) closeViewer();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeViewer();
  });

  // ---- 전체 받기: 브라우저 안에서 zip(무압축)으로 묶어 한 파일로 저장 ----
  var TABLE = (function () {
    var t = [], c, k;
    for (var n = 0; n < 256; n++) {
      c = n;
      for (k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
      t[n] = c >>> 0;
    }
    return t;
  })();
  function crc32(u8) {
    var c = 0xFFFFFFFF;
    for (var i = 0; i < u8.length; i++) c = TABLE[(c ^ u8[i]) & 0xFF] ^ (c >>> 8);
    return (c ^ 0xFFFFFFFF) >>> 0;
  }
  function bytesFromDataURI(uri) {
    var bin = atob(uri.slice(uri.indexOf(',') + 1));
    var u8 = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
    return u8;
  }
  function num(n, len) {
    var a = new Uint8Array(len);
    for (var i = 0; i < len; i++) a[i] = (n >>> (i * 8)) & 0xFF;
    return a;
  }
  function makeZip(entries) {
    var enc = new TextEncoder(), parts = [], central = [], offset = 0;
    entries.forEach(function (e) {
      var name = enc.encode(e.name), crc = crc32(e.data), size = e.data.length;
      var local = [
        num(0x04034b50, 4), num(20, 2), num(0x0800, 2), num(0, 2),
        num(0, 2), num(0, 2), num(crc, 4), num(size, 4), num(size, 4),
        num(name.length, 2), num(0, 2), name
      ];
      local.forEach(function (p) { parts.push(p); });
      parts.push(e.data);
      central.push([
        num(0x02014b50, 4), num(20, 2), num(20, 2), num(0x0800, 2), num(0, 2),
        num(0, 2), num(0, 2), num(crc, 4), num(size, 4), num(size, 4),
        num(name.length, 2), num(0, 2), num(0, 2), num(0, 2), num(0, 2),
        num(0, 4), num(offset, 4), name
      ]);
      offset += 30 + name.length + size;
    });
    var cstart = offset, csize = 0;
    central.forEach(function (rec) {
      rec.forEach(function (p) { parts.push(p); csize += p.length; });
    });
    [num(0x06054b50, 4), num(0, 2), num(0, 2),
     num(entries.length, 2), num(entries.length, 2),
     num(csize, 4), num(cstart, 4), num(0, 2)].forEach(function (p) {
      parts.push(p);
    });
    return new Blob(parts, { type: 'application/zip' });
  }

  var btn = document.getElementById('dl-all');
  btn.addEventListener('click', function () {
    var links = document.querySelectorAll('.item a[download]');
    if (!links.length) { toast('받을 도안이 아직 없어요'); return; }
    btn.disabled = true;
    var old = btn.textContent;
    btn.textContent = '묶는 중…';
    setTimeout(function () {
      try {
        var used = {}, entries = [];
        links.forEach(function (a) {
          var name = a.getAttribute('download');
          if (used[name]) {
            var dot = name.lastIndexOf('.');
            name = name.slice(0, dot) + '-' + (++used[name]) + name.slice(dot);
          } else { used[name] = 1; }
          entries.push({ name: name, data: bytesFromDataURI(a.getAttribute('href')) });
        });
        var url = URL.createObjectURL(makeZip(entries));
        var a = document.createElement('a');
        a.href = url; a.download = '도안모음.zip';
        document.body.appendChild(a); a.click(); a.remove();
        setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
        toast(entries.length + '장을 도안모음.zip 으로 저장했어요');
      } catch (err) {
        toast('저장에 실패했어요: ' + err.message);
      }
      btn.disabled = false; btn.textContent = old;
    }, 30);
  });
})();
</script>
</html>
"""

page = (TPL
        .replace("__TITLE__", html.escape(PAGE_TITLE))
        .replace("__SUB__", PAGE_SUB)
        .replace("__COUNT__", str(len(sheets)))
        .replace("__CARDS__", "\n".join(cards))
        .replace("__SHEETS__", "\n".join(sheets))
        .replace("__EMPTY__", empty_note)
        .replace("__CREDIT__", html.escape(CREDIT)))

with open(OUT, "w", encoding="utf-8") as f:
    f.write(page)

size_mb = os.path.getsize(OUT) / 1024 / 1024
print("완성!  도안 %d장 · 영상 %d개  →  %s  (%.1f MB)"
      % (len(sheets), len(cards), os.path.basename(OUT), size_mb))
if not sheets:
    print("\n※ 도안이미지/ 폴더가 비어 있어요. 그림을 넣고 다시 실행하세요.")
if warn:
    print(warn)
