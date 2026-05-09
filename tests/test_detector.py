import pytest
from detector import detect_items, match_template_items


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


# ── match_template_items 测试 ─────────────────────────────

_TMPL = {"x": 45, "y": 45, "w": 70, "h": 70}  # 包含 5px 背景边距，模拟真实框选


def test_match_finds_all_three_identical_squares(test_image_3_items):
    items = match_template_items(test_image_3_items, template_box=_TMPL, threshold=0.9)
    assert len(items) == 3


def test_match_result_has_required_keys(test_image_3_items):
    items = match_template_items(test_image_3_items, template_box=_TMPL)
    for item in items:
        assert all(k in item for k in ('x', 'y', 'w', 'h'))


def test_match_high_threshold_reduces_results(test_image_3_items):
    low  = match_template_items(test_image_3_items, _TMPL, threshold=0.5)
    high = match_template_items(test_image_3_items, _TMPL, threshold=0.99)
    assert len(high) <= len(low)


def test_match_raises_on_invalid_path():
    with pytest.raises(ValueError, match="Cannot read image"):
        match_template_items("nonexistent.png", {"x": 0, "y": 0, "w": 60, "h": 60})


def test_match_invalid_template_box_returns_empty(test_image_3_items):
    # w=0 的框选应返回空列表而非报错
    items = match_template_items(test_image_3_items, {"x": 50, "y": 50, "w": 0, "h": 60})
    assert items == []
