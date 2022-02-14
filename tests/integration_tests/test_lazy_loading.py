import os
import shutil
import subprocess

import pytest

from zntrack import zn
from zntrack.core.base import Node
from zntrack.utils.lazy_loader import LazyOption


@pytest.fixture
def proj_path(tmp_path):
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    subprocess.check_call(["git", "init"])
    subprocess.check_call(["dvc", "init"])

    return tmp_path


class HelloWorld(Node):
    value = zn.params({"Lorem": "Ipsum"})

    def run(self):
        pass


def test_lazy_load(proj_path):
    hello_world = HelloWorld()
    hello_world.save()

    hello_world = HelloWorld.load(lazy=True)
    assert hello_world.__dict__["value"] is LazyOption
    assert hello_world.value == {"Lorem": "Ipsum"}
