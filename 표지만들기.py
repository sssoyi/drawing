#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""링크 표지 이미지(og.png) 생성기.

카카오톡·인스타 DM·문자에 주소를 붙여넣으면 뜨는 미리보기 그림을 만듭니다.
결과물: og.png (1200x630)  ← 이 파일이 있어야 표지가 뜹니다. 지우지 마세요.

사용법:  python3 표지만들기.py
문구를 바꾸고 싶으면 아래 '설정' 부분만 고치면 됩니다.
"""

import os
from PIL import Image, ImageDraw, ImageFont

# ─────────────────────────── 설정 ───────────────────────────
OUT_NAME = "og.png"

EYEBROW = "엄마가 먼저 찾는"          # 말풍선 안 문구 ("" 로 두면 말풍선 없음)
TITLE = "럭키마미 그림 도안"           # 큰 제목
TITLE_PX = 100                        # 제목이 길면 줄이세요 (한 줄로 들어가야 함)
SUBTITLE = ""                         # 제목 아래 한 줄 (필요할 때만)
HANDLE = "@luckyyy.mommy"
TAGLINE = "공룡 · 바다동물 · 중장비 · 긴급차량 · 도형"

# 페이지와 같은 색 (만들기.py 의 :root 와 맞춰 둘 것)
BG = "#f6f3ee"
INK = "#1c1a17"
MUTED = "#8b8478"
LINE = "#e6e1d8"
ACCENT = "#c2624a"

W, H = 1200, 630        # 카카오·트위터·페이스북 공통 권장 크기
SS = 2                  # 2배로 그린 뒤 줄여서 테두리를 매끈하게
PAD = 96                # 좌우 여백
TOPBAR = 8              # 페이지 맨 위 띠와 같은 역할
# ────────────────────────────────────────────────────────────

HERE = os.path.dirname(os.path.abspath(__file__))
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


def main():
    img = Image.new("RGB", (W * SS, H * SS), BG)
    d = ImageDraw.Draw(img)

    # 맨 위 띠 — 페이지 상단의 테라코타 선과 같은 마감
    d.rectangle([0, 0, W * SS, TOPBAR * SS], fill=ACCENT)

    x0 = PAD * SS
    line_y = H * SS - 118 * SS         # 아래쪽 얇은 가로선

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
    block_h = box_h + (gap if EYEBROW else 0) + (tbot - ttop) + sub_h
    # 완전한 가운데보다 살짝 위. 아래에 계정 줄이 있어 그래야 균형이 맞는다.
    by0 = (TOPBAR * SS + line_y - block_h) / 2 - 16 * SS
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
    title_bottom = ty + tbot

    if SUBTITLE:
        draw_ls(d, (x0, title_bottom + 30 * SS - stop), SUBTITLE, f_sub, MUTED)
        title_bottom += sub_h

    # ── 아래 한 줄: 얇은 가로선 + 계정 + 카테고리 ──────────────
    d.rectangle([x0, line_y, (W - PAD) * SS, line_y + 1 * SS], fill=LINE)

    f_handle = font(28, "semibold")
    htop, hbot = cap_box(d, HANDLE, f_handle)
    hy = line_y + 40 * SS - htop
    draw_ls(d, (x0, hy), HANDLE, f_handle, ACCENT)

    f_tag = font(25)
    gtop, gbot = cap_box(d, TAGLINE, f_tag)
    tag_w = text_w(d, TAGLINE, f_tag)
    # 계정 글자와 밑선을 맞춘다 (윗선이 아니라 바닥 기준)
    gy = (hy + hbot) - gbot
    draw_ls(d, ((W - PAD) * SS - tag_w, gy), TAGLINE, f_tag, MUTED)

    out = os.path.join(HERE, OUT_NAME)
    img.resize((W, H), Image.LANCZOS).save(out, optimize=True)
    print("만들었습니다:", out, f"({os.path.getsize(out) // 1024}KB)",
          f"| 제목 아래 여백 {int((line_y - title_bottom) / SS)}px")


if __name__ == "__main__":
    main()
