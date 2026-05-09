import os
import tempfile
import numpy as np
import cv2
import pytest


@pytest.fixture
def test_image_3_items(tmp_path):
    """白底图片，含3个黑色方块（可被 OpenCV 轮廓检测到）"""
    img = np.ones((400, 600, 3), dtype=np.uint8) * 255
    boxes = [(50, 50, 110, 110), (220, 80, 280, 140), (400, 60, 460, 120)]
    for x1, y1, x2, y2 in boxes:
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 0), -1)
    image_path = tmp_path / 'test_image.png'
    cv2.imwrite(str(image_path), img)
    yield str(image_path)


@pytest.fixture
def blank_image(tmp_path):
    """纯白图片，无物品"""
    img = np.ones((200, 200, 3), dtype=np.uint8) * 255
    image_path = tmp_path / 'blank_image.png'
    cv2.imwrite(str(image_path), img)
    yield str(image_path)
