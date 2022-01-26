import os
import pathlib
import shutil

import pytest

from zntrack import Node, dvc, zn


@pytest.fixture()
def proj_path(tmp_path):
    shutil.copy(__file__, tmp_path)
    os.chdir(tmp_path)
    return tmp_path


class ZnDeps(Node):
    deps = zn.deps()

    def __init__(self, deps=None, **kwargs):
        super().__init__(**kwargs)
        self.deps = deps


def test_zn_deps(proj_path):
    ZnDeps(deps="test.json").save()
    assert ZnDeps.load().deps == "test.json"
    # with pathlib
    ZnDeps(deps=pathlib.Path("test.json")).save()
    assert ZnDeps.load().deps == pathlib.Path("test.json")
    # with list of pathlib
    ZnDeps(deps=[pathlib.Path("test.json"), pathlib.Path("test2.json")]).save()
    assert ZnDeps.load().deps == [pathlib.Path("test.json"), pathlib.Path("test2.json")]


class ParamsAndDeps(Node):
    """Test interferences of different ZnTrackOptions"""

    param = zn.params()
    deps = dvc.deps()

    def __init__(self, deps=None, **kwargs):
        super().__init__(**kwargs)
        if self.is_loaded:
            return
        self.param = deps
        self.deps = deps


def test_params_and_deps(proj_path):
    ParamsAndDeps(deps="test.json").save()
    assert ParamsAndDeps.load().deps == "test.json"
    assert ParamsAndDeps.load().param == "test.json"
    # with pathlib
    ParamsAndDeps(deps=pathlib.Path("test.json")).save()
    assert ParamsAndDeps.load().param == pathlib.Path("test.json")
    assert ParamsAndDeps.load().deps == pathlib.Path("test.json")
    # # with list of pathlib
    ParamsAndDeps(deps=[pathlib.Path("test.json"), pathlib.Path("test2.json")]).save()
    assert ParamsAndDeps.load().deps == [
        pathlib.Path("test.json"),
        pathlib.Path("test2.json"),
    ]
    assert ParamsAndDeps.load().param == [
        pathlib.Path("test.json"),
        pathlib.Path("test2.json"),
    ]
