import os
import shutil

from zntrack import zn


class ChildMethod:
    def __init__(self, param1, param2):
        self.param1 = param1
        self.param2 = param2

    def print(self):
        print(30 * "#")
        print(self.param1)
        print(self.param2)
        print(30 * "#")


class ExampleNode:
    method = zn.Method()

    def __init__(self, method=None):
        self.method = method


def test_save_and_load_method(tmp_path):
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)

    method = ChildMethod("a", "b")

    example_node = ExampleNode(method=method)
    assert example_node.method.param1 == "a"
    assert example_node.method.param2 == "b"

    # assert method == example_node.method
    assert isinstance(method, ChildMethod)
