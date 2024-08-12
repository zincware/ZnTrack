import typing as t


def get_attr_always_list(obj: t.Any, attr: str) -> list:
    value = getattr(obj, attr)
    if not isinstance(value, list):
        value = [value]
    return value
