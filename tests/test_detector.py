import pytest
from detector import detect_items


def test_detects_three_items(test_image_3_items):
    items = detect_items(test_image_3_items)
    assert len(items) == 3


def test_each_item_has_required_keys(test_image_3_items):
    items = detect_items(test_image_3_items)
    for item in items:
        assert 'x' in item
        assert 'y' in item
        assert 'w' in item
        assert 'h' in item


def test_no_items_on_blank_image(blank_image):
    items = detect_items(blank_image)
    assert items == []


def test_min_area_filters_small_noise(test_image_3_items):
    # min_area 设为超大值，应过滤掉所有物品
    items = detect_items(test_image_3_items, min_area=999999)
    assert items == []


def test_raises_on_invalid_path():
    with pytest.raises(ValueError, match="Cannot read image"):
        detect_items("nonexistent.png")


def test_max_area_filters_large_objects(test_image_3_items):
    # 3个方块面积约 3600px，max_area=100 应过滤掉所有物品
    items = detect_items(test_image_3_items, max_area=100)
    assert items == []


def test_coordinate_values_are_positive(test_image_3_items):
    items = detect_items(test_image_3_items)
    for item in items:
        assert item['x'] >= 0 and item['y'] >= 0
        assert item['w'] > 0 and item['h'] > 0
