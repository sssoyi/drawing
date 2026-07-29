#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""도안 이미지 다듬기.

  · 그림 바깥에 둘러진 테두리 네모(프레임)를 지웁니다.
  · 기울어져 있으면 수평으로 바로 세웁니다.
  · 그림 안에 적힌 손글씨를 지웁니다. (아래 GLYPH_ERASE 참고)
  · 남는 흰 여백을 잘라내 그림만 남깁니다.

사용법:  python3 도안다듬기.py

원본은 처음 한 번 도안원본/ 폴더에 그대로 복사해둡니다.
다시 실행하면 언제나 도안원본/ 의 파일을 기준으로 다시 다듬으므로,
여러 번 돌려도 그림이 점점 깎이지 않습니다.
"""

import math
import os
import re
import shutil
import unicodedata

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(HERE, "도안이미지")
RAW_DIR = os.path.join(HERE, "도안원본")

EXT = (".png", ".jpg", ".jpeg", ".webp")
INK = 200          # 이보다 어두우면 '선'으로 본다
GLYPH_INK = 250    # 글씨를 지울 때는 획 둘레의 흐린 부분까지 잡는다
PAD = 40           # 잘라낸 뒤 남길 여백(px)
PAPER = 246        # 이보다 밝으면 종이 바탕으로 보고 완전한 흰색으로 맞춘다
MIN_TILT = 0.15    # 이 각도(도)보다 작으면 굳이 돌리지 않는다

# 그림 안에 글씨가 적혀 있을 때, 그 글씨가 들어 있는 네모를 여기에 적는다.
# 값은 가로·세로 비율(0~1)로 (왼쪽, 위, 오른쪽, 아래).
# 이 네모 안에 통째로 들어가면서 본체 선과 떨어져 있는 조각만 지운다.
# (눈·점처럼 네모 밖에 있는 것은 건드리지 않는다)
GLYPH_ERASE = {
    "티라노": [(0.47, 0.13, 0.74, 0.44)],
    "프테라노돈": [(0.52, 0.24, 0.87, 0.45)],
}

# 선을 직접 손보는 곳. 뾰족한 데를 둥글게 고치는 식으로 쓴다.
#   erase : 지울 네모 (x0, y0, x1, y1)
#   curve : 그 자리를 대신할 곡선 (시작점, 조절점1, 조절점2, 끝점)
#   width : 선 굵기
# ※ 좌표는 '여백을 잘라낸 뒤'의 그림 기준이다. 원본 사진 좌표가 아니다.
#   예)  "트리케라톱스": [dict(erase=(128, 684, 202, 742),
#                          curve=[(141, 681), (172, 714), (192, 710), (186, 681)],
#                          width=11.2, note="주둥이 끝 둥글게")],
TOUCHUP = {}

# 그림 자체가 비뚤게 그려진 경우 여기에 돌릴 각도를 적는다. (도 단위)
#   양수 = 반시계 방향,  음수 = 시계 방향
# 사진이 아니라 그림의 자세라서 자동으로는 못 잰다. 눈으로 보고 숫자를 고치면 된다.
ROTATE = {
    # 발이 바닥에 나란히 놓이도록 잰 값 (발 접지점 두 곳을 이은 선의 기울기)
    "브라키오사우루스": -14.7,
    "스테고사우루스": -6.4,
    "트리케라톱스": -19.0,
    "안킬로사우루스": -26.5,
    "파키케팔로사우루스": 9.0,
    # 티라노는 두 발이 한 덩어리로 붙어 있어 잴 수 없다. 이미 서 있으므로 그대로 둔다.
}


def key(stem):
    """'01-티라노' → '티라노'. 맥의 자모 분리(NFD)도 합쳐서 비교한다."""
    return re.sub(r"^\s*\d+\s*[-_.)]\s*", "",
                  unicodedata.normalize("NFC", stem)).strip()


def ink_mask(img):
    return np.asarray(img.convert("L")) < INK


def find_frame(mask):
    """이미지 거의 전체를 감싸는 컴포넌트(테두리 네모)를 찾는다."""
    H, W = mask.shape
    lab, n = ndimage.label(mask, structure=np.ones((3, 3)))
    if n == 0:
        return None, None, None
    for i, (sy, sx) in enumerate(ndimage.find_objects(lab), start=1):
        if (sx.stop - sx.start) > 0.88 * W and (sy.stop - sy.start) > 0.88 * H:
            return lab, i, (sy, sx)
    return lab, None, None


def frame_tilt(frame_mask, sy, sx):
    """테두리 윗변의 기울기로 사진이 얼마나 돌아갔는지 잰다."""
    x0 = sx.start + int(0.1 * (sx.stop - sx.start))
    x1 = sx.start + int(0.9 * (sx.stop - sx.start))
    depth = max(8, (sy.stop - sy.start) // 12)
    band = frame_mask[sy.start:sy.start + depth, x0:x1]
    xs, ys = [], []
    for c in range(band.shape[1]):
        col = np.where(band[:, c])[0]
        if col.size:
            xs.append(c)
            ys.append(col[0])
    if len(xs) < 30:
        return 0.0
    slope = np.polyfit(np.asarray(xs, float), np.asarray(ys, float), 1)[0]
    return math.degrees(math.atan(slope))


def erase_glyphs(img, rects):
    """지정한 네모 안에 통째로 들어간 '본체가 아닌' 조각을 지운다."""
    # 획 둘레의 흐린 회색(안티에일리어싱)까지 한 덩어리로 잡아야 유령 테두리가 안 남는다
    mask = np.asarray(img.convert("L")) < GLYPH_INK
    H, W = mask.shape
    lab, n = ndimage.label(mask, structure=np.ones((3, 3)))
    if n == 0:
        return img, 0
    sizes = ndimage.sum(mask, lab, range(1, n + 1))
    main = int(np.argmax(sizes)) + 1
    objs = ndimage.find_objects(lab)

    drop = np.zeros(n + 1, dtype=bool)
    for i in range(1, n + 1):
        if i == main:
            continue
        sy, sx = objs[i - 1]
        for l, t, r, b in rects:
            if (sx.start >= l * W and sx.stop <= r * W
                    and sy.start >= t * H and sy.stop <= b * H):
                drop[i] = True
                break

    if not drop.any():
        return img, 0
    gone = drop[lab]
    gone = ndimage.binary_dilation(gone, structure=np.ones((3, 3)), iterations=2)
    arr = np.asarray(img).copy()
    arr[gone] = (255, 255, 255)
    return Image.fromarray(arr), int(drop.sum())


def apply_touchup(img, jobs, up=4):
    """지정한 자리를 지우고 부드러운 곡선으로 다시 잇는다.

    4배로 키운 조각 위에 그린 뒤 되돌려서, 계단처럼 각지지 않게 한다.
    """
    def bezier(p, t):
        u = 1 - t
        return (u**3 * p[0][0] + 3*u*u*t * p[1][0]
                + 3*u*t*t * p[2][0] + t**3 * p[3][0],
                u**3 * p[0][1] + 3*u*u*t * p[1][1]
                + 3*u*t*t * p[2][1] + t**3 * p[3][1])

    done = []
    for job in jobs:
        pad = int(job["width"]) + 12
        xs = [p[0] for p in job["curve"]] + [job["erase"][0], job["erase"][2]]
        ys = [p[1] for p in job["curve"]] + [job["erase"][1], job["erase"][3]]
        box = (max(min(xs) - pad, 0), max(min(ys) - pad, 0),
               min(max(xs) + pad, img.width), min(max(ys) + pad, img.height))
        x0, y0, x1, y1 = box
        patch = img.crop(box).resize(((x1 - x0) * up, (y1 - y0) * up), Image.LANCZOS)
        d = ImageDraw.Draw(patch)

        e = job["erase"]
        d.rectangle([(e[0] - x0) * up, (e[1] - y0) * up,
                     (e[2] - x0) * up, (e[3] - y0) * up], fill=255)

        pts = [(p[0] - x0, p[1] - y0) for p in job["curve"]]
        r = job["width"] / 2 * up
        for i in range(801):
            cx, cy = bezier(pts, i / 800)
            cx, cy = cx * up, cy * up
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=0)

        img.paste(patch.resize((x1 - x0, y1 - y0), Image.LANCZOS), (x0, y0))
        done.append(job.get("note", "손봄"))
    return img, done


def tidy(path, stem=""):
    img = Image.open(path).convert("RGB")

    # 1) 기울기 보정 — 테두리가 있으면 그 윗변을 기준으로 잰다
    lab, frame, box = find_frame(ink_mask(img))
    note = []
    if frame is not None:
        angle = frame_tilt(lab == frame, *box)
        if abs(angle) >= MIN_TILT:
            img = img.rotate(angle, resample=Image.BICUBIC,
                             expand=True, fillcolor=(255, 255, 255))
            note.append("기울기 %+.2f° 보정" % -angle)
            lab, frame, box = find_frame(ink_mask(img))

    # 2) 테두리 지우기
    mask = ink_mask(img)
    if frame is not None:
        mask = mask & (lab != frame)
        arr = np.asarray(img).copy()
        arr[lab == frame] = (255, 255, 255)
        img = Image.fromarray(arr)
        note.append("테두리 제거")

    # 3) 그림 안 손글씨 지우기
    rects = GLYPH_ERASE.get(key(stem))
    if rects:
        img, gone = erase_glyphs(img, rects)
        if gone:
            note.append("글씨 %d조각 지움" % gone)
        mask = ink_mask(img)

    # 3-b) 그림 자세가 비뚤면 손으로 정한 각도만큼 돌린다
    turn = ROTATE.get(key(stem))
    if turn:
        img = img.rotate(turn, resample=Image.BICUBIC,
                         expand=True, fillcolor=(255, 255, 255))
        note.append("%+g° 돌림" % turn)
        mask = ink_mask(img)

    if not mask.any():
        return img, ["내용 없음"]

    # 4) 여백 잘라내기
    ys, xs = np.where(mask)
    H, W = mask.shape
    box = (max(int(xs.min()) - PAD, 0), max(int(ys.min()) - PAD, 0),
           min(int(xs.max()) + PAD + 1, W), min(int(ys.max()) + PAD + 1, H))
    img = img.crop(box)
    note.append("여백 정리 → %d×%d" % img.size)

    # 4-b) 선 직접 손보기 (좌표가 잘라낸 뒤 기준이라 여기서 한다)
    jobs = TOUCHUP.get(key(stem))
    if jobs:
        img = img.convert("L")
        img, done = apply_touchup(img, jobs)
        note.extend(done)

    # 5) 바탕을 완전한 흰색으로 통일한다.
    #    종이 바탕이 253쯤이라 글씨를 지운 자리(순백 255)만 더 밝아 유령처럼 비친다.
    a = np.asarray(img).copy()
    if a.ndim == 3:
        a[a[:, :, :3].min(2) >= PAPER] = 255
    else:
        a[a >= PAPER] = 255
    img = Image.fromarray(a)

    # 6) 색이 없는 선 그림이면 흑백으로 저장한다 (보기엔 똑같고 용량이 크게 준다)
    if a.ndim == 3 and int(np.abs(a[:, :, :3].max(2).astype(int)
                                  - a[:, :, :3].min(2).astype(int)).max()) <= 12:
        img = img.convert("L")
    return img, note


def main():
    os.makedirs(RAW_DIR, exist_ok=True)

    # 새로 넣은 그림은 먼저 도안원본/ 에 챙겨둔다
    for f in sorted(os.listdir(IMG_DIR)):
        if f.lower().endswith(EXT) and not f.startswith("."):
            raw = os.path.join(RAW_DIR, f)
            if not os.path.exists(raw):
                shutil.copy2(os.path.join(IMG_DIR, f), raw)

    # 다듬기는 언제나 도안원본/ 을 기준으로 한다
    names = sorted(f for f in os.listdir(RAW_DIR)
                   if f.lower().endswith(EXT) and not f.startswith("."))
    if not names:
        print("도안이미지/ 폴더가 비어 있어요.")
        return

    for f in names:
        raw = os.path.join(RAW_DIR, f)
        stem = os.path.splitext(f)[0]
        img, note = tidy(raw, stem)                     # 늘 원본에서 다시 다듬는다
        out = stem + ".png"
        dst, old = os.path.join(IMG_DIR, out), os.path.join(IMG_DIR, f)
        img.save(dst, optimize=True)
        # 맥은 대소문자를 안 가려서 .PNG 와 .png 가 같은 파일이다.
        # 이름만 다르다고 지우면 방금 저장한 파일을 지우게 되므로 실제 파일로 비교한다.
        if os.path.exists(old) and not os.path.samefile(old, dst):
            os.remove(old)
        print("· %-24s %s" % (stem, " / ".join(note)))

    print("\n다 됐습니다. 원본은 도안원본/ 에 그대로 있어요.")


if __name__ == "__main__":
    main()
