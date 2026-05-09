import os
import tempfile
import numpy as np
import cv2
import pytest


@pytest.fixture
def test_image_3_items():
    """白底图片，含3个黑色方块（可被 OpenCV 轮廓检测到）"""
    img = np.ones((400, 600, 3), dtype=np.uint8) * 255
    boxes = [(50, 50, 110, 110), (220, 80, 280, 140), (400, 60, 460, 120)]
    for x1, y1, x2, y2 in boxes:
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 0), -1)
    f = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    cv2.imwrite(f.name, img)
    yield f.name
    os.unlink(f.name)


@pytest.fixture
def blank_image():
    """纯白图片，无物品"""
    img = np.ones((200, 200, 3), dtype=np.uint8) * 255
    f = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    cv2.imwrite(f.name, img)
    yield f.name
    os.unlink(f.name)
