import cv2
import numpy as np
from typing import Optional


def match_template_items(
    image_path: str,
    template_box: dict,
    threshold: float = 0.7,
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
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray_tmpl = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    if float(gray_tmpl.std()) < 2.0:
        return []

    result = cv2.matchTemplate(gray_img, gray_tmpl, cv2.TM_CCOEFF_NORMED)

    # 用模板尺寸的膨胀核找局部极大值，替代传统 NMS
    nms_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (tw, th))
    dilated = cv2.dilate(result, nms_kernel, borderType=cv2.BORDER_REPLICATE)
    peaks_mask = (result >= threshold) & (result >= dilated - 1e-6)
    ys, xs = np.where(peaks_mask)

    items = []
    for x, y in zip(xs.tolist(), ys.tolist()):
        patch = gray_img[y:y + th, x:x + tw]
        if float(patch.std()) < 2.0:
            continue
        items.append({"x": int(x), "y": int(y), "w": tw, "h": th})
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
