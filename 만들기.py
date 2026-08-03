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

# 제목은 두 줄. 윗줄에 손그림 밑줄이 들어갑니다.
TITLE_TOP = "엄마가 먼저 찾는"
TITLE_MAIN = "럭키마미 그림 도안"
PAGE_TITLE = (TITLE_TOP + " " + TITLE_MAIN).replace("*", "")  # 브라우저 탭 이름
PAGE_SUB = ('<span class="cats">공룡 · 바다동물 · 중장비 · 긴급차량 · 도형</span>'
            "고민 없이 바로 출력해서 놀아주는 엄마표 그림놀이!<br>"
            "릴스 영상 보며 따라 그리면 더 재미있어요.")
# 섹션 제목 옆 작은 안내
VIDEO_HINT = "영상을 누르면 재생됩니다"

CREDIT = "@luckyyy.mommy"

# 링크를 카톡·DM·문자에 붙여넣었을 때 뜨는 미리보기.
# 표지 그림은 '표지만들기.py' 로 만듭니다 (og.png).
PAGE_URL = "https://luckyyymommy.com/drawing/"
OG_IMAGE = PAGE_URL + "og.png"
OG_VERSION = "1"   # 표지를 새로 만들면 이 숫자를 올리세요. 카톡이 옛 그림을 계속 물고 있습니다.
OG_DESC = ("공룡 · 바다동물 · 중장비 · 긴급차량 · 도형 도안을 무료로 나눕니다. "
           "바로 출력해서 아이와 함께 그려보세요.")
# 맨 아래 저작권 문구. " | " 자리에서 줄이 바뀝니다.
COPYRIGHT = "ⓒ 2026 luckyyy.mommy. All rights reserved."
TERMS = ("도안은 마음껏 출력해서 아이와 즐겁게 사용해 주세요. | "
         "다만 파일을 재배포하거나 상업적으로 이용하는 것은 금지합니다.")
SHEET_CREDIT = "ⓒ luckyyy.mommy"   # 도안 A4 맨 아래에 작게 들어가는 한 줄
INSTAGRAM_URL = "https://www.instagram.com/luckyyy.mommy/"

# 맨 아래 '인증샷 보내주세요' 칸
FUNNEL_TITLE = "럭키마미 도안 200% 즐기는 방법!"
# " | " 를 넣은 자리에서 줄이 바뀝니다.
FUNNEL_STEPS = [
    "도안을 예쁘게 출력해서 아이와 함께 신나게 놀아주세요.",
    "아이가 완성한 작품이나 즐겁게 놀이하는 모습을 | 사진으로 남겨주세요.",
    "인스타그램 스토리에 @luckyyy.mommy 를 | 태그해서 자랑해 주세요!",
]
# 줄 단위로 적습니다. 좁은 화면에서는 한 줄씩 끊어서 보여줍니다.
FUNNEL_NOTE = [
    "보내주신 소중한 인증샷은",
    "다음 도안을 만드는 데 정말 큰 힘이 됩니다",
    "아이들과 함께한 따뜻한 순간들, 저도 같이 구경하러 갈게요!",
]

# 이모지 대신 직접 그린 픽토그램 (선 그림 톤에 맞춘 1.5px 라인)
ICONS = {
    "gift": ('<rect x="3.2" y="9.4" width="17.6" height="11.4" rx="2"/>'
             '<path d="M3.2 13.6h17.6M12 9.4v11.4"/>'
             '<path d="M12 9.4S9.6 9.3 8.2 8.6C7 8 6.9 6.5 7.8 5.8c1-.8 2.3-.2 3 1 .7 1.1 1.2 2.6 1.2 2.6Z"/>'
             '<path d="M12 9.4s2.4-.1 3.8-.8c1.2-.6 1.3-2.1.4-2.8-1-.8-2.3-.2-3 1-.7 1.1-1.2 2.6-1.2 2.6Z"/>'),
    "instagram": ('<rect x="3.4" y="3.4" width="17.2" height="17.2" rx="5"/>'
                  '<circle cx="12" cy="12" r="4.1"/>'
                  '<circle cx="17.1" cy="6.9" r="1.05" fill="currentColor" stroke="none"/>'),
    "share": ('<circle cx="17.8" cy="5.4" r="2.6"/><circle cx="6.2" cy="12" r="2.6"/>'
              '<circle cx="17.8" cy="18.6" r="2.6"/>'
              '<path d="M8.5 10.8 15.5 6.6M8.5 13.2 15.5 17.4"/>'),
    "heart": ('<path d="M12 20.3S3.7 15.1 3.7 9.4c0-2.5 2-4.4 4.3-4.4 1.8 0 3.2 1 4 2.3.8-1.3 2.2-2.3 4-2.3'
              ' 2.3 0 4.3 1.9 4.3 4.4 0 5.7-8.3 10.9-8.3 10.9Z"/>'),
}


def icon(name, size=22, cls="ico"):
    return ('<svg class="%s" width="%d" height="%d" viewBox="0 0 24 24" fill="none" '
            'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" '
            'stroke-linejoin="round" aria-hidden="true">%s</svg>'
            % (cls, size, size, ICONS[name]))

IMG_EXT = (".png", ".jpg", ".jpeg", ".webp", ".heic", ".heif", ".gif")
MAX_PX = 1800  # 긴 변 기준 리사이즈 (A4 출력에 충분)

# 도안 아래에 한글 제목과 함께 적을 영어 단어. (한글 제목 → 영어)
# 여기에 없는 도안은 한글 제목만 나옵니다.
ENGLISH = {
    "티라노사우루스": "Tyrannosaurus",
    "브라키오사우루스": "Brachiosaurus",
    "스테고사우루스": "Stegosaurus",
    "트리케라톱스": "Triceratops",
    "안킬로사우루스": "Ankylosaurus",
    "파키케팔로사우루스": "Pachycephalosaurus",
    "프테라노돈": "Pteranodon",
    "고래": "Whale",
    "상어": "Shark",
    "문어": "Octopus",
    "가오리": "Stingray",
    "물개": "Seal",
    "포크레인": "Excavator",
    "불도저": "Bulldozer",
    "덤프트럭": "Dump Truck",
    "래미콘": "Concrete Mixer",
    "경찰차": "Police Car",
    "구급차": "Ambulance",
    "소방차": "Fire Truck",
    "기차": "Train",
    "배": "Ship",
    "비행기": "Airplane",
    "자전거": "Bicycle",
}

# 도안을 묶어서 보여줄 섹션. 위에서부터 이 순서로 나옵니다.
# 목록에 없는 도안은 맨 아래 '그 밖에' 로 모입니다.
SECTIONS = [
    ("공룡", ["티라노사우루스", "브라키오사우루스", "스테고사우루스", "트리케라톱스",
             "안킬로사우루스", "파키케팔로사우루스", "프테라노돈"]),
    ("바다동물", ["고래", "상어", "문어", "가오리", "물개"]),
    ("중장비", ["포크레인", "불도저", "덤프트럭", "래미콘"]),
    ("긴급차량", ["경찰차", "구급차", "소방차"]),
    ("탈것", ["기차", "배", "비행기", "자전거"]),
]

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

# 영상별 인스타 릴스 주소. 적어두면 영상 아래 '릴스 보기' 버튼이 생깁니다.
# 주소를 안 적은 영상은 버튼이 안 나옵니다.
VIDEO_LINK = {
    "dino-1":    "https://www.instagram.com/reel/DNxtkn05rvV/",   # 공룡 그리기 1탄
    "dino-2":    "https://www.instagram.com/reel/DQZEiuwkq7h/",   # 공룡 그리기 2탄
    "sea":       "https://www.instagram.com/reel/DOIWJc1Ew9D/",   # 바다동물 그리기
    "machine":   "https://www.instagram.com/reel/DNPpf1bz_v-/",   # 중장비 그리기
    "emergency": "https://www.instagram.com/reel/DNfq3f4TeqT/",   # 경찰차 · 구급차 · 소방차
    "shapes":    "https://www.instagram.com/reel/DOf3FNkE4g8/",   # 도형으로 그리기
}


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


def long_side(path):
    """sips로 이미지의 긴 변 길이를 잰다. 못 재면 0."""
    try:
        out = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", path],
                             check=True, capture_output=True, text=True).stdout
        nums = [int(n) for n in re.findall(r"pixel(?:Width|Height):\s*(\d+)", out)]
        return max(nums) if nums else 0
    except Exception:
        return 0


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
        # sips -Z 는 작은 그림을 억지로 키운다. 선만 흐려지고 용량만 커지니 그냥 둔다.
        if 0 < long_side(src) <= MAX_PX:
            return src
        dst = os.path.join(workdir, base + ext)
        cmd = ["sips", "-Z", str(MAX_PX), src, "--out", dst]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        if os.path.getsize(dst) > 0:
            return dst
    except Exception:
        pass
    return src


def a4_font(size, bold=False):
    from PIL import ImageFont
    for path, idx in (("/System/Library/Fonts/AppleSDGothicNeo.ttc", 3 if bold else 0),
                      ("/System/Library/Fonts/Supplemental/AppleGothic.ttf", 0)):
        try:
            return ImageFont.truetype(path, size, index=idx)
        except Exception:
            continue
    return None


def compose_a4(src, ko, en, out_path):
    """그림 위 · 한글/영문 제목 아래로 A4 한 장을 만들어 저장한다.

    화면에 보이는 것과 받는 파일이 같아야 해서, 웹에서 글씨를 얹지 않고
    이미지 자체에 구워 넣는다. (휴대폰에서 사진으로 저장해도 제목이 남는다)
    """
    from PIL import Image, ImageDraw

    W, H = 1240, 1754                       # A4 150dpi
    mx, mtop, mbot = 87, 123, 62
    cw = W - mx * 2
    ko_px, en_px, cr_px = int(cw * .08), int(cw * .05), int(cw * .019)
    f_ko, f_en, f_cr = a4_font(ko_px, True), a4_font(en_px), a4_font(cr_px)
    if not f_ko:
        return False

    sheet = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(sheet)

    def line_h(font, text):
        b = d.textbbox((0, 0), text or "가", font=font)
        return b[3] - b[1]

    cap_top_gap, ko_en_gap, cr_gap = int(cw * .05), int(cw * .016), int(cw * .035)
    h_ko = line_h(f_ko, ko)
    h_en = line_h(f_en, en) if en else 0
    h_cr = line_h(f_cr, SHEET_CREDIT)
    cap_h = (cap_top_gap + h_ko + (ko_en_gap + h_en if en else 0) + cr_gap + h_cr)

    art = Image.open(src).convert("L")
    box_w, box_h = cw, H - mtop - mbot - cap_h
    k = min(box_w / art.width, box_h / art.height)
    art = art.resize((max(1, int(art.width * k)), max(1, int(art.height * k))),
                     Image.LANCZOS)
    sheet.paste(art, (mx + (box_w - art.width) // 2,
                      mtop + (box_h - art.height) // 2))

    y = mtop + box_h + cap_top_gap

    def center(text, font, fill, top):
        b = d.textbbox((0, 0), text, font=font)
        d.text(((W - (b[2] - b[0])) // 2 - b[0], top - b[1]), text, font=font, fill=fill)

    center(ko, f_ko, 28, y)
    y += h_ko
    if en:
        y += ko_en_gap
        center(en, f_en, 85, y)
        y += h_en
    y += cr_gap
    center(SHEET_CREDIT, f_cr, 160, y)

    sheet.save(out_path, optimize=True)
    return True


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

by_title = {}
workdir = tempfile.mkdtemp()
try:
    for f in files:
        src = os.path.join(IMG_DIR, f)
        ko = pretty_title(f)
        title = html.escape(ko)
        en = ENGLISH.get(nfc(ko), "")

        # 제목까지 넣은 A4 한 장을 만들어 그걸 화면에도 쓰고 받기에도 쓴다.
        a4 = os.path.join(workdir, "a4-" + os.path.splitext(f)[0] + ".png")
        try:
            made = compose_a4(src, ko, en, a4)
        except Exception as e:
            made, a4_err = False, e
            print("  ※ %s : A4 만들기 실패(%s). 그림만 넣습니다." % (ko, e))
        uri = data_uri(a4 if made else web_copy(src, workdir))

        dname = html.escape(ko + ".png" if made else download_name(f))
        by_title[nfc(ko)] = """      <figure class="item">
        <div class="sheet"><img src="{uri}" alt="{title}"></div>
        <figcaption>
          <span class="cap-name">{title}</span>
          <a class="btn-ghost" download="{dname}">받기</a>
        </figcaption>
      </figure>""".format(uri=uri, title=title, dname=dname)
finally:
    shutil.rmtree(workdir, ignore_errors=True)

# 섹션별로 묶는다. 목록에 없는 도안은 '그 밖에' 로.
used, groups = set(), []
for name, titles in SECTIONS:
    picked = [by_title[nfc(t)] for t in titles if nfc(t) in by_title]
    used.update(nfc(t) for t in titles)
    if picked:
        groups.append((name, picked))
rest = [by_title[t] for t in by_title if t not in used]
if rest:
    groups.append(("그 밖에", rest))

sheets = []
for name, items in groups:
    sheets.append('      <h3 class="group">%s <span>%d장</span></h3>\n%s'
                  % (html.escape(name), len(items), "\n".join(items)))

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

cards, vid_bytes = [], 0
for f in vids:
    stem = nfc(os.path.splitext(f)[0])
    poster = os.path.join(POSTER_DIR, stem + ".jpg")
    pos = ' poster="%s"' % data_uri(poster) if os.path.exists(poster) else ""
    label = html.escape(VIDEO_LABEL.get(stem, stem))
    vid_bytes += os.path.getsize(os.path.join(vid_base, f))
    reels = VIDEO_LINK.get(stem, "")
    reel_btn = ('<a class="btn-ghost" href="%s" target="_blank" rel="noopener">릴스 보기</a>'
                % html.escape(reels)) if reels else ""
    cards.append("""      <article class="clip">
        <div class="vwrap">
          <video controls preload="none" playsinline{pos} data-title="{label}">
            <source src="{src}" type="video/mp4">
          </video>
        </div>
        <h3>{label}</h3>
        <div class="clip-acts">
          <a class="btn-ghost vdl" href="{src}" download="{dl}">받기</a>
          {reel}
        </div>
      </article>""".format(pos=pos, src=quote(prefix) + quote(f), label=label,
                          dl=html.escape(label + ".mp4"), reel=reel_btn))

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
<meta name="description" content="__OG_DESC__">
<link rel="canonical" href="__PAGE_URL__">
<!-- 링크 미리보기(카톡·인스타 DM·페북·문자). 주소는 반드시 전체 주소여야 합니다. -->
<meta property="og:type" content="website">
<meta property="og:site_name" content="럭키마미">
<meta property="og:locale" content="ko_KR">
<meta property="og:url" content="__PAGE_URL__">
<meta property="og:title" content="__TITLE__">
<meta property="og:description" content="__OG_DESC__">
<meta property="og:image" content="__OG_IMAGE__">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="__TITLE__">
<meta name="twitter:card" content="summary_large_image">
<style>
  :root {
    --ink:#1c1a17; --muted:#8b8478; --line:#e6e1d8;
    --paper:#fffdf9; --bg:#f6f3ee; --accent:#c2624a;
    --accent-2:#566b5d;   /* 공유 버튼. 테라코타와 짝이 되는 차분한 초록 */
  }
  * { box-sizing:border-box; }
  body {
    margin:0; background:var(--bg); color:var(--ink);
    font-family:'Apple SD Gothic Neo','Pretendard',-apple-system,system-ui,sans-serif;
    line-height:1.6; -webkit-font-smoothing:antialiased;
  }
  .wrap { max-width:1080px; margin:0 auto; padding:0 20px 80px; }

  /* 화면 맨 위를 마감하는 얇은 띠. 스크롤해도 그대로 남아 종이의 위쪽 테두리 역할을 한다. */
  .topbar {
    position:fixed; top:0; left:0; right:0; height:3px;
    background:var(--accent); z-index:40;   /* 전체화면 뷰어(50)보다는 아래 */
  }

  header { padding:64px 0 40px; text-align:center; }
  .page-title {
    display:flex; flex-direction:column; align-items:center; gap:19px;
    margin:0 0 14px; font-weight:700;
  }
  /* 말풍선 */
  .page-title .eyebrow {
    position:relative; display:inline-block;
    font-size:22px; font-weight:600; color:var(--accent);
    letter-spacing:.01em; white-space:nowrap;
    line-height:1;
    /* 한글 글자는 기준선 위쪽에 몰려 있어, 위아래 여백을 같게 주면 위로 붙어 보인다.
       실제 잉크 범위를 재서 위 .59em / 아래 .41em 로 맞췄다. */
    padding:.59em .95em .41em;
    border:1.8px solid var(--accent);
    border-radius:1.2em;
    /* 통통 튀는 효과. 한 번 크게 + 한 번 작게 튀고 나머지 시간은 가만히 있는다.
       계속 움직이면 글씨를 읽는 데 방해가 되므로 3.6초에 한 번만 튄다.
       transform-origin 을 아래로 둬서 착지할 때 살짝 눌리는 느낌이 난다. */
    transform-origin:50% 100%;
    animation:bubble-bounce 3.6s ease-in-out infinite;
  }
  @keyframes bubble-bounce {
    0%, 58%, 100% { transform:translateY(0) scale(1, 1); }
    64%           { transform:translateY(0) scale(1.03, .96); }   /* 웅크리기 */
    72%           { transform:translateY(-9px) scale(.99, 1.03); } /* 크게 튀기 */
    80%           { transform:translateY(0) scale(1.02, .97); }   /* 착지 */
    88%           { transform:translateY(-4px) scale(1, 1.01); }  /* 작게 한 번 더 */
    94%           { transform:translateY(0) scale(1.01, .99); }
  }
  /* 화면 움직임을 줄여달라고 설정한 사람에게는 애니메이션을 끈다 */
  @media (prefers-reduced-motion: reduce) {
    .page-title .eyebrow { animation:none; }
  }
  .page-title .eyebrow::after {      /* 아래를 가리키는 꼬리 */
    content:""; position:absolute; left:50%; bottom:-8px;
    width:13px; height:13px; background:var(--bg);
    border-right:1.8px solid var(--accent);
    border-bottom:1.8px solid var(--accent);
    border-bottom-right-radius:4px;
    transform:translateX(-50%) rotate(45deg);
  }
  .page-title .main {
    font-size:34px; letter-spacing:-.03em; line-height:1.25;
    word-break:keep-all;
  }
  header p {
    margin:0 auto; color:var(--muted); font-size:15px; max-width:520px;
    word-break:keep-all; overflow-wrap:break-word;
  }
  /* 카테고리 줄은 아래 소개글과 구분되게 진하게 */
  .cats {
    display:block; color:var(--ink); font-weight:600; font-size:16px;
    letter-spacing:-.01em; margin-bottom:9px;
  }
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
  h2 .hint {
    font-weight:400; letter-spacing:0; opacity:.72; margin-left:5px;
    word-break:keep-all;
  }
  section { margin-top:56px; }

  .clips { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:22px; }
  .clip { min-width:0; }   /* video 기본 폭 300px 이 칸을 밀지 않게 */
  .clip video { min-width:0; }
  .vwrap { position:relative; }
  .clip video {
    width:100%; aspect-ratio:9/16; object-fit:cover; display:block;
    border-radius:14px; background:#111; border:1px solid var(--line);
  }
  .clip h3 {
    font-size:14px; font-weight:500; margin:10px 2px 0;
    word-break:keep-all; overflow-wrap:break-word;
  }
  .clip-acts { display:flex; gap:6px; margin:8px 2px 0; }
  .clip-acts .btn-ghost { flex:1; text-align:center; }

  .grid { display:grid; grid-template-columns:repeat(2,1fr); gap:28px 24px; }
  .item { margin:0; min-width:0; }   /* 긴 제목이 칸 너비를 밀지 않게 */
  .group {
    grid-column:1/-1; margin:34px 0 2px; font-size:26px; font-weight:600;
    letter-spacing:-.02em; display:flex; align-items:baseline; gap:12px;
  }
  .group:first-child { margin-top:0; }
  .group span { font-size:14px; font-weight:400; color:var(--muted); }
  /* A4 세로 한 장. 제목은 이미지 안에 이미 들어 있다. */
  .sheet {
    aspect-ratio:1/1.4142; background:#fff; border:1px solid var(--line);
    border-radius:4px; display:flex; align-items:center; justify-content:center;
    overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,.05);
  }
  .sheet img { width:100%; height:100%; object-fit:contain; display:block; }
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

  /* 맨 아래 인증샷 안내 — 상자로 가두지 않고 얇은 선으로만 구분한다 */
  #funnel {
    margin-top:74px; padding-top:44px; border-top:1px solid var(--line);
  }
  /* 왼쪽 단: 제목 → 문구 → 버튼,  오른쪽 단: 1·2·3 단계 */
  .funnel {
    display:grid; grid-template-columns:minmax(0,.92fr) minmax(0,1.08fr);
    column-gap:52px; align-items:start;
  }
  .funnel-title { grid-column:1; grid-row:1; }
  .steps        { grid-column:2; grid-row:1 / span 3; }
  .funnel-note  { grid-column:1; grid-row:2; }
  .funnel-btns  { grid-column:1; grid-row:3; }
  .funnel-title {
    font-size:25px; font-weight:700; line-height:1.35; letter-spacing:-.03em;
    color:var(--ink); margin:0; padding:0; border:0; text-align:left;
    text-wrap:balance; word-break:keep-all;
  }

  /* 번호는 색 채운 동그라미가 아니라 활자로. 글줄 첫 줄 기준선에 맞춘다. */
  .steps { list-style:none; margin:0; padding:0;
           display:flex; flex-direction:column; gap:17px; }
  .steps li {
    display:grid; grid-template-columns:25px minmax(0,1fr); align-items:baseline;
    font-size:14.5px; line-height:1.65;
    word-break:keep-all; overflow-wrap:break-word; text-align:left;
  }
  .steps .n {
    color:var(--accent); font-size:14.5px; font-weight:600;
    font-variant-numeric:tabular-nums;
  }

  .funnel-note {
    margin:26px 0 0; text-align:left;
    color:var(--muted); font-size:14px; line-height:1.8;
    word-break:keep-all; overflow-wrap:break-word;
  }
  .funnel-note .ln { display:inline; }
  .funnel-note .ln + .ln::before { content:" "; }
  .funnel-note .ln.nl { display:block; }
  .funnel-note .heart { color:var(--accent); vertical-align:-2px; margin-left:5px; }

  .funnel-btns {
    margin-top:26px;
    display:flex; gap:11px; align-items:center; flex-wrap:wrap;
  }
  .funnel-btns .btn {
    text-decoration:none; display:inline-flex; align-items:center; gap:8px;
    background:var(--accent); color:#fff;
  }
  .funnel-btns .btn-share { background:var(--accent-2); }
  .funnel-btns .ico { flex:none; }

  /* 공유 메뉴 — 버튼 위로 뜨는 작은 목록 */
  .share-wrap { position:relative; display:inline-flex; }
  .share-menu {
    position:absolute; left:0; bottom:calc(100% + 9px); z-index:20;
    min-width:186px; background:var(--paper); border:1px solid var(--line);
    border-radius:8px; padding:5px; box-shadow:0 6px 22px rgba(28,26,23,.11);
    display:flex; flex-direction:column;
  }
  .share-menu[hidden] { display:none; }
  .share-menu button {
    appearance:none; border:0; background:none; cursor:pointer; font:inherit;
    font-size:13.5px; color:var(--ink); text-align:left;
    padding:9px 11px; border-radius:5px; transition:background .12s;
  }
  .share-menu button:hover, .share-menu button:focus-visible {
    background:rgba(28,26,23,.055); outline:none;
  }
  .share-hint {
    margin:1px 11px 6px; font-size:11.5px; color:var(--muted); line-height:1.4;
  }

  footer {
    margin-top:56px; padding-top:26px; border-top:1px solid var(--line);
    text-align:center; color:var(--muted);
    display:flex; flex-direction:column; gap:7px;
  }
  footer p { margin:0; word-break:keep-all; }
  footer .ig { font-size:13.5px; color:var(--ink); }
  footer .copy { font-size:12.5px; }
  footer .terms { font-size:12px; line-height:1.7; opacity:.8; }
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
    header { padding:44px 0 24px; }   /* 띠 아래로 말풍선이 숨 쉴 만큼 */
    .page-title { gap:15px; margin-bottom:12px; }
    .page-title .eyebrow { font-size:15.5px; border-width:1.6px; }
    .page-title .eyebrow::after { width:11px; height:11px; bottom:-7px;
      border-right-width:1.6px; border-bottom-width:1.6px; }
    .page-title .main { font-size:24px; }
    header p { font-size:13.5px; }
    .btn { padding:10px 17px; font-size:13.5px; }
    section { margin-top:40px; }

    /* 영상: 한 줄에 3개 썸네일 */
    .clips { grid-template-columns:repeat(3,minmax(0,1fr)); gap:9px; }
    .clip video { border-radius:9px; pointer-events:none; }
    .clip-acts { gap:4px; margin-top:6px; }
    .clip-acts .btn-ghost { font-size:10.5px; padding:4px 4px; }
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

    h2 .hint { display:block; margin:3px 0 0; font-size:12px; }
    #funnel { margin-top:48px; padding-top:32px; }
    .funnel { grid-template-columns:1fr; row-gap:22px; }
    .funnel-title, .steps, .funnel-note, .funnel-btns {
      grid-column:auto; grid-row:auto;
    }
    .funnel-note { margin-top:4px; }
    .funnel-title { font-size:20px; }
    .steps { gap:15px; }
    .steps li { font-size:13.5px; grid-template-columns:22px minmax(0,1fr); }
    .steps .n { font-size:13.5px; }
    .funnel-note { font-size:13px; margin-top:26px; }
    .funnel-note .ln { display:block; }
    .funnel-note .ln + .ln::before { content:none; }
    .funnel-btns { margin-top:22px; gap:10px; align-items:stretch; }
    .share-wrap { display:flex; }
    .share-wrap > .btn { width:100%; justify-content:center; }
    .share-menu { left:0; right:0; min-width:0; }

    /* 도안: 영상과 같이 가로 3열 */
    .grid { grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px 9px; }
    .group { font-size:17px; margin:20px 0 0; gap:8px; }
    .group span { font-size:12px; }
    .sheet { border-radius:3px; }
    figcaption {
      display:flex; flex-direction:column; align-items:stretch;
      gap:5px; margin-top:7px; padding:0;
    }
    .cap-name {
      font-size:11.5px; line-height:1.3; text-align:center;
      overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
    }
    .btn-ghost { font-size:11px; padding:4px 6px; text-align:center; }
  }

  @page { size:A4; margin:0; }
  @media print {
    body { background:#fff; }
    .topbar, header, .tools, #videos, #funnel, footer, figcaption, #toast { display:none !important; }
    .wrap { max-width:none; padding:0; }
    section { margin:0; }
    h2 { display:none; }
    .grid { display:block; }
    .item { break-after:page; page-break-after:always; }
    .sheet {
      width:210mm; height:297mm; border:0; border-radius:0; box-shadow:none;
      padding:0; background:#fff;
    }
    .group { display:none; }
  }
</style>

<div class="topbar"></div>

<div class="wrap">
  <header>
    <h1 class="page-title">
      <span class="eyebrow">__TITLE_TOP__</span>
      <span class="main">__TITLE_MAIN__</span>
    </h1>
    <p>__SUB__</p>
    <div class="tools">
      <button class="btn" id="dl-all">도안 전체 받기 (__COUNT__장)</button>
      <button class="btn btn-line" id="dl-vids">영상 전체 받기 (__VCOUNT__개 · __VSIZE__)</button>
    </div>
  </header>

  <section id="videos">
    <h2>영상 보고 따라 그리기 <span class="hint">__VHINT__</span></h2>
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

  <section id="funnel">
    <div class="funnel">
      <h2 class="funnel-title">__F_TITLE__</h2>
      <ol class="steps">
__F_STEPS__
      </ol>
      <p class="funnel-note">__F_NOTE__</p>
      <div class="funnel-btns">
        <a class="btn" href="__IG__" target="_blank" rel="noopener">__IG_ICON__<span>인스타그램 놀러가기</span></a>
        <span class="share-wrap">
          <button class="btn btn-share" id="share-page" aria-haspopup="true" aria-expanded="false">__SH_ICON__<span>육아 동지에게 공유하기</span></button>
          <div class="share-menu" id="share-menu" hidden>
            <button type="button" data-act="copy">링크 복사하기</button>
            <p class="share-hint">복사해서 카카오톡에 붙여넣어 주세요</p>
            <button type="button" data-act="sms">문자로 보내기</button>
            <button type="button" data-act="mail">메일로 보내기</button>
          </div>
        </span>
      </div>
    </div>
  </section>

  <footer>
    <p class="ig">__CREDIT__</p>
    <p class="copy">__COPYRIGHT__</p>
    <p class="terms">__TERMS__</p>
  </footer>
</div>

<div id="viewer" hidden>
  <p id="viewer-title"></p>
  <button id="viewer-close" aria-label="닫기">✕</button>
  <video controls playsinline preload="auto"></video>
</div>

<div id="toast"></div>

<script>
(function () {
  // 받기 링크는 그림과 같은 데이터를 쓴다. 파일에 두 번 넣으면 용량이 두 배가 되므로
  // 페이지가 열릴 때 그림의 주소를 그대로 링크에 붙여준다.
  document.querySelectorAll('.item').forEach(function (item) {
    var a = item.querySelector('a[download]'), img = item.querySelector('img');
    if (!a || !img) return;
    a.href = img.src;

    // 아이폰에서 data: 링크를 그냥 누르면 '파일' 앱으로 들어간다.
    // 공유 시트를 띄워주면 '이미지 저장'으로 사진첩에 바로 담을 수 있다.
    a.addEventListener('click', function (e) {
      var phone = window.matchMedia('(max-width: 860px)').matches;
      if (navigator.canShare) {
        var bin = atob(img.src.slice(img.src.indexOf(',') + 1));
        var u8 = new Uint8Array(bin.length);
        for (var i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
        var file = new File([u8], a.getAttribute('download'), { type: 'image/png' });
        if (navigator.canShare({ files: [file] })) {
          e.preventDefault();
          navigator.share({ files: [file] }).catch(function () {});
          return;
        }
      }
      // 공유 시트를 못 쓰는 경우(주소가 http 이거나 지원 안 하는 브라우저)
      if (phone) toast('사진첩에 담으려면 그림을 길게 눌러 \u2018사진에 추가\u2019');
    });
  });

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
    if (!viewer || viewer.hidden) return;   // 아직 못 찾았으면 할 일이 없다
    vv.pause();
    vv.removeAttribute('src');
    vv.load();
    viewer.hidden = true;
    document.body.style.overflow = '';
  }

  document.querySelectorAll('.clip').forEach(function (clip) {
    clip.addEventListener('click', function (ev) {
      if (ev.target.closest('.clip-acts')) return;   // 받기·릴스 버튼은 그대로 두기
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

  // 육아 동지에게 공유하기
  // 휴대폰처럼 기기 공유창을 쓸 수 있으면 그걸 띄우고,
  // 그럴 수 없는 PC 에서는 직접 만든 목록을 열어 고르게 한다.
  // 영상 받기 — 휴대폰이면 공유창을 띄워 사진 앱에 담을 수 있게 한다
  document.querySelectorAll('a.vdl').forEach(function (a) {
    a.addEventListener('click', function (e) {
      if (!navigator.canShare) return;              // 안 되면 그냥 내려받기
      e.preventDefault();
      var old = a.textContent;
      a.textContent = '준비 중…';
      fetch(a.getAttribute('href'))
        .then(function (r) { return r.blob(); })
        .then(function (b) {
          var file = new File([b], a.getAttribute('download'), { type: 'video/mp4' });
          // 파일 공유 자체를 못 하는 기기(주로 PC)는 내려받기로 되돌린다
          if (!navigator.canShare({ files: [file] })) throw { name: 'NoFileShare' };
          return navigator.share({ files: [file] });
        })
        .catch(function (err) {
          var name = err && err.name;
          if (name === 'AbortError') return;           // 사용자가 공유창을 닫은 것
          if (name === 'NoFileShare') {
            var l = document.createElement('a');
            l.href = a.getAttribute('href');
            l.download = a.getAttribute('download');
            document.body.appendChild(l); l.click(); l.remove();
            return;
          }
          // 사파리에서 링크로 영상을 열면 저장이 아니라 재생으로 빠지므로,
          // 공유창이 실패했을 때 내려받기로 되돌리지 않고 방법을 알려준다.
          toast('저장이 안 됐어요. 영상을 길게 눌러 저장해 주세요');
        })
        .then(function () { a.textContent = old; });
    });
  });

  // 영상 전체 받기
  // 아이폰 사파리는 링크를 눌러도 영상이 저장되지 않고 그냥 재생돼 버린다.
  // 그래서 공유창을 쓸 수 있는 기기에서는 두 번 눌러 받는다.
  // (iOS 는 사용자가 누른 직후에만 공유창을 허용해서, 영상을 다 불러온 뒤 띄우면 막힌다.
  //  그래서 첫 번째 탭에서 불러오기만 하고, 두 번째 탭에서 공유창을 띄운다.)
  var vidBtn = document.getElementById('dl-vids');
  if (vidBtn) {
    var vidLabel = vidBtn.textContent;
    var vidFiles = null;                 // 불러와 둔 영상들. 두 번째 탭에서 쓴다

    function readyLabel(n) { return '사진 앱에 담기 (' + n + '개)'; }

    // PC — 예전 방식대로 하나씩 순서대로 내려받는다 (한 덩어리로 묶으면 버거워서)
    function downloadAll(links) {
      vidBtn.disabled = true;
      links.forEach(function (src, i) {
        setTimeout(function () {
          var a = document.createElement('a');
          a.href = src.getAttribute('href');
          a.download = src.getAttribute('download');
          document.body.appendChild(a); a.click(); a.remove();
          vidBtn.textContent = '저장 중… (' + (i + 1) + '/' + links.length + ')';
          if (i === links.length - 1) {
            setTimeout(function () {
              vidBtn.disabled = false;
              vidBtn.textContent = vidLabel;
              toast(links.length + '개를 모두 저장했어요');
            }, 900);
          }
        }, i * 900);
      });
    }

    // 휴대폰 — 영상을 하나씩 차례로 불러온다 (한꺼번에 받으면 메모리가 버겁다)
    function loadAll(links) {
      var files = [];
      return links.reduce(function (chain, a, i) {
        return chain.then(function () {
          vidBtn.textContent = '불러오는 중… (' + (i + 1) + '/' + links.length + ')';
          return fetch(a.getAttribute('href'))
            .then(function (r) { return r.blob(); })
            .then(function (b) {
              files.push(new File([b], a.getAttribute('download'), { type: 'video/mp4' }));
            });
        });
      }, Promise.resolve()).then(function () { return files; });
    }

    vidBtn.addEventListener('click', function () {
      var links = [].slice.call(document.querySelectorAll('a.vdl'));
      if (!links.length) { toast('받을 영상이 없어요'); return; }
      // 손가락으로 쓰는 기기에서만 공유창 방식. PC 는 예전처럼 바로 내려받는다
      var phone = window.matchMedia('(hover: none) and (pointer: coarse)').matches;
      if (!phone || !navigator.canShare) { downloadAll(links); return; }

      if (vidFiles) {                    // 두 번째 탭 — 바로 공유창을 띄운다
        navigator.share({ files: vidFiles })
          .then(function () { toast('사진 앱에 담았어요'); })
          .catch(function (err) {
            if (!err || err.name !== 'AbortError') {
              toast('저장이 안 됐어요. 영상을 하나씩 받아주세요');
            }
          });
        return;
      }

      vidBtn.disabled = true;
      loadAll(links).then(function (files) {
        if (!navigator.canShare({ files: files })) {   // 파일 공유를 못 하면 내려받기로
          vidBtn.textContent = vidLabel;
          downloadAll(links);
          return;
        }
        vidFiles = files;
        vidBtn.disabled = false;
        vidBtn.textContent = readyLabel(files.length);
        toast('준비됐어요. 한 번 더 눌러주세요');
      }).catch(function () {
        vidBtn.disabled = false;
        vidBtn.textContent = vidLabel;
        toast('영상을 불러오지 못했어요. 하나씩 받아주세요');
      });
    });
  }

  var shareBtn = document.getElementById('share-page');
  var shareMenu = document.getElementById('share-menu');
  var SHARE_TEXT = '아이랑 바로 출력해서 놀 수 있는 그림 도안 나눔이에요!';

  function pageUrl() { return location.href.split('#')[0]; }

  function openMenu(on) {
    shareMenu.hidden = !on;
    shareBtn.setAttribute('aria-expanded', on ? 'true' : 'false');
  }

  function copyLink() {
    var url = pageUrl();
    if (navigator.clipboard) {
      navigator.clipboard.writeText(url)
        .then(function () { toast('링크를 복사했어요. 붙여넣기 해서 보내주세요'); })
        .catch(function () { window.prompt('아래 주소를 복사해 주세요', url); });
    } else {
      window.prompt('아래 주소를 복사해 주세요', url);
    }
  }

  if (shareBtn && shareMenu) {
    shareBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      if (navigator.share) {            // 카카오톡·메시지 등 기기 공유창
        navigator.share({ title: document.title, text: SHARE_TEXT, url: pageUrl() })
          .catch(function () {});
        return;
      }
      openMenu(shareMenu.hidden);
    });

    shareMenu.addEventListener('click', function (e) {
      var act = e.target.getAttribute && e.target.getAttribute('data-act');
      if (!act) return;
      var url = pageUrl();
      var body = encodeURIComponent(SHARE_TEXT + '\n' + url);
      if (act === 'copy') copyLink();
      else if (act === 'sms') location.href = 'sms:?&body=' + body;
      else if (act === 'mail') {
        location.href = 'mailto:?subject=' + encodeURIComponent(document.title)
                      + '&body=' + body;
      }
      openMenu(false);
    });

    document.addEventListener('click', function () { openMenu(false); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') openMenu(false);
    });
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
        .replace("__TITLE_TOP__", re.sub(
            r"\*(.+?)\*", r'<em class="mark">\1</em>', html.escape(TITLE_TOP)))
        .replace("__TITLE_MAIN__", html.escape(TITLE_MAIN))
        .replace("__TITLE__", html.escape(PAGE_TITLE))
        .replace("__PAGE_URL__", html.escape(PAGE_URL))
        .replace("__OG_IMAGE__", html.escape(OG_IMAGE + "?v=" + OG_VERSION))
        .replace("__OG_DESC__", html.escape(OG_DESC))
        .replace("__SUB__", PAGE_SUB)
        .replace("__COUNT__", str(len(by_title)))
        .replace("__VCOUNT__", str(len(cards)))
        .replace("__VSIZE__", "%.0fMB" % (vid_bytes / 1024 / 1024))
        .replace("__CARDS__", "\n".join(cards))
        .replace("__SHEETS__", "\n".join(sheets))
        .replace("__EMPTY__", empty_note)
        .replace("__VHINT__", "(%s)" % html.escape(VIDEO_HINT))
        .replace("__CREDIT__", html.escape(CREDIT))
        .replace("__COPYRIGHT__", html.escape(COPYRIGHT))
        .replace("__TERMS__", "<br>".join(html.escape(t.strip())
                                          for t in TERMS.split("|")))
        .replace("__F_TITLE__", html.escape(FUNNEL_TITLE))
        .replace("__F_STEPS__", "\n".join(
            "        <li><span class=\"n\">%d</span><span>%s</span></li>"
            % (i, "<br>".join(html.escape(part.strip())
                              for part in t.split("|")))
            for i, t in enumerate(FUNNEL_STEPS, 1)))
        .replace("__IG_ICON__", icon("instagram", 18))
        .replace("__SH_ICON__", icon("share", 18))
        .replace("__F_NOTE__", "".join(
            '<span class="ln%s">%s%s</span>'
            % (" nl" if i == len(FUNNEL_NOTE) - 1 else "", html.escape(t),
               icon("heart", 15, "ico heart") if i == len(FUNNEL_NOTE) - 2 else "")
            for i, t in enumerate(FUNNEL_NOTE)))
        .replace("__IG__", html.escape(INSTAGRAM_URL)))

with open(OUT, "w", encoding="utf-8") as f:
    f.write(page)

size_mb = os.path.getsize(OUT) / 1024 / 1024
print("완성!  도안 %d장 · 영상 %d개  →  %s  (%.1f MB)"
      % (len(by_title), len(cards), os.path.basename(OUT), size_mb))
if not sheets:
    print("\n※ 도안이미지/ 폴더가 비어 있어요. 그림을 넣고 다시 실행하세요.")
if warn:
    print(warn)
