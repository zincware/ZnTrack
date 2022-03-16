import pytest

from zntrack.descriptor import Descriptor


class ExampleCls:
    desc = Descriptor()


def test_get_descriptor():
    assert isinstance(ExampleCls.desc, Descriptor)


def test_descriptor_name():
    descriptor = ExampleCls.desc
    assert descriptor.name == "desc"


def test_descriptor_owner():
    descriptor = ExampleCls.desc
    assert descriptor.owner == ExampleCls


@pytest.mark.parametrize("access", ("get", "set"))
def test_get_instance(access):
    desc = ExampleCls.desc

    cls = ExampleCls()
    if access == "set":
        cls.desc = 25
    elif access == "get":
        _ = cls.desc

    assert desc.instance == cls


def test_descriptor_set():
    desc = ExampleCls.desc
    cls = ExampleCls()
    cls.desc = 42
    assert cls.__dict__[desc.name] == 42


def test_descriptor_get():
    desc = ExampleCls.desc
    cls = ExampleCls()
    cls.__dict__[desc.name] = 42
    assert cls.desc == 42
