import cv2
import numpy as np
from typing import Optional


def _rotate_image(img: np.ndarray, angle: float) -> np.ndarray:
    """旋转图像，自动扩展画布以保留全部内容"""
    h, w = img.shape[:2]
    cx, cy = w / 2, h / 2
    M = cv2.getRotationMatrix2D((cx, cy), angle, 1.0)
    cos_a, sin_a = abs(M[0, 0]), abs(M[0, 1])
    new_w = int(h * sin_a + w * cos_a)
    new_h = int(h * cos_a + w * sin_a)
    M[0, 2] += new_w / 2 - cx
    M[1, 2] += new_h / 2 - cy
    return cv2.warpAffine(img, M, (new_w, new_h))


def _clahe(gray: np.ndarray) -> np.ndarray:
    """CLAHE 局部对比度归一化，减少光照不均的影响"""
    return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)


def match_template_items(
    image_path: str,
    template_box: dict,
    threshold: float = 0.35,
) -> list:
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")

    ih, iw = img.shape[:2]
    tx = max(0, int(template_box['x']))
    ty = max(0, int(template_box['y']))
    tw = min(int(template_box['w']), iw - tx)
    th = min(int(template_box['h']), ih - ty)

    if tw <= 0 or th <= 0:
        return []

    template = img[ty:ty + th, tx:tx + tw]
    gray_img = _clahe(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
    gray_tmpl = _clahe(cv2.cvtColor(template, cv2.COLOR_BGR2GRAY))

    if float(gray_tmpl.std()) < 2.0:
        return []

    # 多角度 × 多尺度匹配，收集所有候选中心点
    candidates = []  # [(cx, cy, score)]
    scales = [0.85, 1.0, 1.15]
    for angle in range(0, 360, 45):
        rot_tmpl = _rotate_image(gray_tmpl, angle) if angle != 0 else gray_tmpl
        for scale in scales:
            if scale != 1.0:
                t = cv2.resize(rot_tmpl, None, fx=scale, fy=scale,
                               interpolation=cv2.INTER_LINEAR)
            else:
                t = rot_tmpl
            rh, rw = t.shape[:2]
            if rh >= ih or rw >= iw or rh < 3 or rw < 3:
                continue
            result = cv2.matchTemplate(gray_img, t, cv2.TM_CCOEFF_NORMED)
            ys, xs = np.where(result >= threshold)
            for x, y in zip(xs.tolist(), ys.tolist()):
                candidates.append((x + rw / 2, y + rh / 2, float(result[y, x])))

    # 贪心 NMS：按分数降序，中心点距离 < max(tw,th)*0.5 则抑制
    candidates.sort(key=lambda c: c[2], reverse=True)
    nms_dist = max(tw, th) * 0.5
    items = []
    for cx, cy, _ in candidates:
        if any(abs(cx - r['x'] - r['w'] / 2) < nms_dist and
               abs(cy - r['y'] - r['h'] / 2) < nms_dist
               for r in items):
            continue
        x0 = max(0, int(cx - tw / 2))
        y0 = max(0, int(cy - th / 2))
        patch = gray_img[y0:y0 + th, x0:x0 + tw]
        if float(patch.std()) < 2.0:
            continue
        items.append({"x": x0, "y": y0, "w": tw, "h": th})
    return items


def detect_items(
    image_path: str,
    min_area: int = 500,
    max_area: Optional[int] = None,
    block_size: int = 11,
    c_value: int = 2,
    morph_iterations: int = 0,
) -> list:
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")

    h, w = img.shape[:2]
    if max_area is None:
        max_area = int(w * h * 0.8)

    # block_size 必须为奇数且 >= 3
    block_size = max(3, block_size | 1)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    binary = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        block_size, c_value
    )

    if morph_iterations > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=morph_iterations)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    items = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if min_area <= area <= max_area:
            x, y, cw, ch = cv2.boundingRect(cnt)
            items.append({"x": x, "y": y, "w": cw, "h": ch})

    return items
