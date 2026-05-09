import cv2
from typing import Optional


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
