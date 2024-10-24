import typing as t

import pytest

import zntrack


class AcceptDeps(zntrack.Node):
    deps: t.Any = zntrack.deps()


def test_generic_deps(proj_path):
    with zntrack.Project() as proj:
        AcceptDeps(deps=1)

    with pytest.raises(ValueError):
        proj.build()


def test_generic_deps_list(proj_path):
    with zntrack.Project() as proj:
        AcceptDeps(deps=[1, 2, 3])

    with pytest.raises(ValueError):
        proj.build()
