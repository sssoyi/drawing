#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""링크 표지 이미지(og.png) 생성기.

카카오톡·인스타 DM·문자에 주소를 붙여넣으면 뜨는 미리보기 그림을 만듭니다.
결과물: og.png (1200x630)  ← 이 파일이 있어야 표지가 뜹니다. 지우지 마세요.

사용법:  python3 표지만들기.py
문구를 바꾸고 싶으면 아래 '설정' 부분만 고치면 됩니다.
"""

import os
import unicodedata
from PIL import Image, ImageDraw, ImageFont

# ─────────────────────────── 설정 ───────────────────────────
OUT_NAME = "og.png"

EYEBROW = "엄마가 먼저 찾는"          # 말풍선 안 문구 ("" 로 두면 말풍선 없음)
TITLE = "럭키마미 그림 도안"           # 큰 제목
TITLE_PX = 100                        # 제목이 길면 줄이세요 (한 줄로 들어가야 함)
SUBTITLE = ""                         # 제목 아래 한 줄 (필요할 때만)
HANDLE = "@luckyyy.mommy"
TAGLINE = "공룡 · 바다동물 · 중장비 · 긴급차량 · 탈것"

# 제목 아래에 늘어놓을 대표 도안. 도안이미지/ 안의 파일 이름 앞부분만 적으면 됩니다.
# 순서가 곧 왼쪽부터의 차례. 빈 목록([])으로 두면 그림 줄이 없어집니다.
ILLUST = ["01-티라노", "08-고래", "13-포크레인", "19-소방차", "22-비행기"]
ILLUST_H = 108        # 그림 한 개의 높이(px). 줄이 넘치면 자동으로 더 줄어듭니다.
ILLUST_GAP = 34       # 그림 사이 간격

# 페이지와 같은 색 (만들기.py 의 :root 와 맞춰 둘 것)
BG = "#f6f3ee"
INK = "#1c1a17"
MUTED = "#8b8478"
ACCENT = "#c2624a"

W, H = 1200, 630        # 카카오·트위터·페이스북 공통 권장 크기
SS = 2                  # 2배로 그린 뒤 줄여서 테두리를 매끈하게
PAD = 96                # 좌우 여백
BAND_H = 104            # 맨 아래 테라코타 띠(계정·카테고리가 올라앉는 자리)의 높이
# ────────────────────────────────────────────────────────────

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(HERE, "도안이미지")
FONT_TTC = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
FACE = {"regular": 0, "medium": 2, "semibold": 4, "bold": 6}


def font(px, weight="regular"):
    return ImageFont.truetype(FONT_TTC, px * SS, index=FACE[weight])


def text_w(d, s, f, ls=0):
    """자간(ls, px 단위)을 넣은 글자 폭."""
    if not s:
        return 0
    w = sum(d.textlength(ch, font=f) for ch in s)
    return w + ls * SS * (len(s) - 1)


def draw_ls(d, xy, s, f, fill, ls=0):
    """자간을 직접 벌려 가며 한 글자씩 그린다. PIL 에는 자간 기능이 없다."""
    x, y = xy
    for ch in s:
        d.text((x, y), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f) + ls * SS
    return x


def cap_box(d, s, f):
    """글자가 실제로 차지하는 위/아래 (앵커 기준 상대값). 광학 정렬용."""
    b = d.textbbox((0, 0), s or "가", font=f)
    return b[1], b[3]


def mix(c1, c2, t):
    """색 두 개를 t 비율로 섞는다 (t=0 이면 c1)."""
    a = Image.new("RGB", (1, 1), c1).getpixel((0, 0))
    b = Image.new("RGB", (1, 1), c2).getpixel((0, 0))
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def load_line_art(name):
    """도안 한 장을 '선만 남은' 투명 그림으로 읽는다.

    도안은 흰 바탕에 검은 선이다. 밝기를 그대로 뒤집어 투명도로 쓰면
    흰 바탕은 사라지고 선의 부드러운 가장자리는 그대로 남는다.
    """
    # 맥 파일 이름은 NFD 로 풀어져 있어서 그냥 비교하면 한글이 안 맞는다.
    key = unicodedata.normalize("NFC", name)
    hit = None
    for f in sorted(os.listdir(IMG_DIR)):
        if unicodedata.normalize("NFC", f).startswith(key):
            hit = os.path.join(IMG_DIR, f)
            break
    if not hit:
        raise SystemExit(f"'{name}' 로 시작하는 도안을 {IMG_DIR} 에서 못 찾았어요.")

    gray = Image.open(hit).convert("L")
    alpha = gray.point(lambda v: 255 - v)          # 검은 선 = 불투명
    alpha = alpha.crop(alpha.getbbox())            # 둘레 흰 여백 잘라내기
    return alpha


def draw_illust_row(img, y_center, x0, max_w):
    """대표 도안을 한 줄로 늘어놓는다. 높이를 맞추고 왼쪽부터 채운다."""
    arts = [load_line_art(n) for n in ILLUST]
    h = ILLUST_H * SS
    gap = ILLUST_GAP * SS
    for _ in range(40):                            # 줄이 넘치면 조금씩 줄인다
        widths = [max(1, round(a.width * h / a.height)) for a in arts]
        if sum(widths) + gap * (len(arts) - 1) <= max_w:
            break
        h *= 0.97
    ink = Image.new("RGB", (1, 1), INK).getpixel((0, 0))

    x = x0
    for a, w in zip(arts, widths):
        a = a.resize((w, int(round(h))), Image.LANCZOS)
        # 줄여 놓으면 선이 옅어진다. 진하기를 올려 원래 굵기처럼 보이게.
        a = a.point(lambda v: min(255, int(v * 1.55)))
        piece = Image.new("RGBA", a.size, ink + (0,))
        piece.putalpha(a)
        img.paste(piece, (int(x), int(y_center - a.height / 2)), piece)
        x += w + gap
    return int(h / SS)


def main():
    img = Image.new("RGB", (W * SS, H * SS), BG)
    d = ImageDraw.Draw(img)

    x0 = PAD * SS
    band_y = (H - BAND_H) * SS         # 맨 아래 띠가 시작하는 높이

    # ── 글자 덩어리 높이를 먼저 재서 위아래 여백을 반씩 나눈다 ──
    f_eye = font(30, "semibold")
    f_title = font(TITLE_PX, "bold")
    f_sub = font(27)
    bw = 2.4 * SS                      # 말풍선 테두리 두께
    # 한글은 기준선 위쪽에 몰려 있어 위아래 패딩을 같게 주면 위로 붙어 보인다.
    # 페이지 말풍선과 같은 .59 / .41 비대칭으로 광학 중앙을 맞춘다.
    ex = 30 * SS * 1.05                # 말풍선 좌우 안쪽 여백
    top_pad, bot_pad = 30 * SS * 0.62, 30 * SS * 0.44
    t_top, t_bot = cap_box(d, EYEBROW, f_eye)
    box_h = ((t_bot - t_top) + top_pad + bot_pad) if EYEBROW else 0
    gap = 44 * SS                      # 말풍선과 제목 사이
    ttop, tbot = cap_box(d, TITLE, f_title)
    stop, sbot = cap_box(d, SUBTITLE, f_sub)
    sub_h = (30 * SS + (sbot - stop)) if SUBTITLE else 0
    art_h = (46 * SS + ILLUST_H * SS) if ILLUST else 0
    block_h = box_h + (gap if EYEBROW else 0) + (tbot - ttop) + sub_h + art_h
    by0 = (band_y - block_h) / 2
    by1 = by0 + box_h

    if EYEBROW:
        # ── 말풍선 (테두리만. 소희 취향: 채움 반전보다 테두리) ────
        eye_w = text_w(d, EYEBROW, f_eye, ls=-0.4)
        bx1 = x0 + eye_w + ex * 2
        d.rounded_rectangle([x0, by0, bx1, by1], radius=box_h / 2,
                            outline=ACCENT, width=int(round(bw)))
        draw_ls(d, (x0 + ex, by0 + top_pad - t_top), EYEBROW, f_eye, ACCENT, ls=-0.4)

        # 꼬리 — 아래를 가리키는 V. 말풍선 밑줄을 바탕색으로 끊고 그 자리에 잇는다.
        hw, depth = 11 * SS, 11 * SS
        tcx = x0 + 46 * SS
        d.rectangle([tcx - hw + bw * 0.6, by1 - bw, tcx + hw - bw * 0.6, by1 + bw], fill=BG)
        d.line([(tcx - hw, by1 - bw * 0.7), (tcx, by1 + depth), (tcx + hw, by1 - bw * 0.7)],
               fill=ACCENT, width=int(round(bw)), joint="curve")
        by1 += gap

    # ── 큰 제목 ────────────────────────────────────────────────
    ty = by1 - ttop
    draw_ls(d, (x0, ty), TITLE, f_title, INK, ls=-TITLE_PX * 0.03)
    bottom = ty + tbot

    if SUBTITLE:
        draw_ls(d, (x0, bottom + 30 * SS - stop), SUBTITLE, f_sub, MUTED)
        bottom += sub_h

    # ── 대표 도안 한 줄 ────────────────────────────────────────
    if ILLUST:
        h = draw_illust_row(img, bottom + (46 + ILLUST_H / 2) * SS,
                            x0, (W - PAD * 2) * SS)
        bottom += (46 + h) * SS

    # ── 맨 아래 띠: 계정 + 카테고리 ────────────────────────────
    # 미리보기 상자는 모서리가 둥글게 잘리므로, 띠는 위가 아니라 아래에 둔다.
    d.rectangle([0, band_y, W * SS, H * SS], fill=ACCENT)
    on_band = mix(BG, ACCENT, 0.06)          # 띠 위 글자색 (순백보다 부드럽게)
    on_band_dim = mix(BG, ACCENT, 0.42)

    f_handle = font(28, "semibold")
    htop, hbot = cap_box(d, HANDLE, f_handle)
    # 한글·영문 모두 광학 중앙에 오도록 실제 글자 높이 기준으로 앉힌다.
    hy = band_y + (BAND_H * SS - (hbot - htop)) / 2 - htop
    draw_ls(d, (x0, hy), HANDLE, f_handle, on_band)

    f_tag = font(25)
    gtop, gbot = cap_box(d, TAGLINE, f_tag)
    tag_w = text_w(d, TAGLINE, f_tag)
    gy = (hy + hbot) - gbot                  # 계정 글자와 밑선을 맞춘다
    draw_ls(d, ((W - PAD) * SS - tag_w, gy), TAGLINE, f_tag, on_band_dim)

    out = os.path.join(HERE, OUT_NAME)
    img.resize((W, H), Image.LANCZOS).save(out, optimize=True)
    print("만들었습니다:", out, f"({os.path.getsize(out) // 1024}KB)",
          f"| 띠까지 남은 여백 {int((band_y - bottom) / SS)}px")


if __name__ == "__main__":
    main()
