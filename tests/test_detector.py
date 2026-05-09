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


def test_large_block_size_still_returns_list(test_image_3_items):
    items = detect_items(test_image_3_items, block_size=101)
    assert isinstance(items, list)


def test_even_block_size_is_coerced_to_odd(test_image_3_items):
    # block_size=10 应被强制转为 11，不应抛出异常
    items = detect_items(test_image_3_items, block_size=10)
    assert isinstance(items, list)


def test_morph_iterations_reduces_noise(test_image_3_items):
    items_no_morph = detect_items(test_image_3_items, morph_iterations=0)
    items_with_morph = detect_items(test_image_3_items, morph_iterations=3)
    # 形态学处理不应使结果变成非列表
    assert isinstance(items_with_morph, list)
    # 降噪后检测数量 ≤ 未降噪数量（小方块图可能不变，但不应更多）
    assert len(items_with_morph) <= len(items_no_morph)
