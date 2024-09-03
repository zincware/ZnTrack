import pytest

from zntrack.utils.misc import sort_and_deduplicate


def test_mixed_types():
    data = [
        "b.yaml",
        "a.yaml",
        {"c.yaml": {"cache": False}},
    ]
    expected_result = [
        "a.yaml",
        "b.yaml",
        {"c.yaml": {"cache": False}},
    ]
    assert sort_and_deduplicate(data) == expected_result


def test_all_strings():
    data = ["z.yaml", "a.yaml", "b.yaml", "a.yaml"]
    expected_result = ["a.yaml", "b.yaml", "z.yaml"]
    assert sort_and_deduplicate(data) == expected_result


def test_all_dicts():
    data = [
        {"a.yaml": {"cache": False}},
        {"c.yaml": {"cache": True}},
        {"b.yaml": {"cache": True}},
        {"a.yaml": {"cache": False}},  # Duplicate
    ]
    expected_result = [
        {"a.yaml": {"cache": False}},
        {"b.yaml": {"cache": True}},
        {"c.yaml": {"cache": True}},
    ]
    assert sort_and_deduplicate(data) == expected_result


def test_empty():
    data = []
    expected_result = []
    assert sort_and_deduplicate(data) == expected_result


def test_different_parameter():
    data = [
        {"a.yaml": {"cache": False}},
        {"a.yaml": {"cache": True}},
    ]
    with pytest.raises(ValueError):
        sort_and_deduplicate(data)


def test_different_parameter_and_type():
    data = [
        "a.yaml",
        {"a.yaml": {"cache": True}},
    ]
    with pytest.raises(ValueError):
        sort_and_deduplicate(data)


def test_different_parameter_and_type_rev():
    data = [
        {"a.yaml": {"cache": True}},
        "a.yaml",
    ]
    with pytest.raises(ValueError):
        sort_and_deduplicate(data)
