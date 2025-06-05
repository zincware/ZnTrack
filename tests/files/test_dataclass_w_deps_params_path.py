import dataclasses
import json
import pathlib
from pathlib import Path

import yaml

import zntrack

CWD = pathlib.Path(__file__).parent.resolve()


class Model:
    """Base Model class"""


@dataclasses.dataclass
class ModelWithParamsPath(Model):
    """Model with parameters"""

    params: dict
    config: str | Path | list[str | Path] = zntrack.params_path()


@dataclasses.dataclass
class ModelWithDepsPath(Model):
    """Model with dependencies"""

    params: dict
    files: str | Path | list[str | Path] = zntrack.deps_path()


@dataclasses.dataclass
class ModelWithParamsAndDepsPath(Model):
    """Model with parameters and dependencies"""

    params: dict
    config: str | Path | list[str | Path] = zntrack.params_path()
    files: str | Path | list[str | Path] = zntrack.deps_path()


class NodeWithModel(zntrack.Node):
    """Node with model"""

    model: Model | list[Model] = zntrack.deps()


def test_node_with_dc_model_params_deps(proj_path):
    project = zntrack.Project()

    a1 = ModelWithParamsPath(params={"a": 1}, config="config.yaml")
    a2 = ModelWithParamsPath(params={"a": 1}, config=Path("config.yaml"))
    b1 = ModelWithDepsPath(params={"a": 1}, files="file.txt")
    b2 = ModelWithDepsPath(params={"a": 1}, files=Path("file.txt"))
    c = ModelWithParamsAndDepsPath(
        params={"a": 1},
        config=["config.yaml", Path("config2.yaml")],
        files=["file.txt", Path("file2.txt")],
    )

    with project:
        NodeWithModel(model=a1)
        NodeWithModel(model=a2)
        NodeWithModel(model=b1)
        NodeWithModel(model=b2)
        NodeWithModel(model=c)
        NodeWithModel(model=[c])

    project.build()

    assert json.loads(
        (CWD / "zntrack_config" / "dataclass_w_deps_params_path.json").read_text()
    ) == json.loads((proj_path / "zntrack.json").read_text())
    assert yaml.safe_load(
        (CWD / "dvc_config" / "dataclass_w_deps_params_path.yaml").read_text()
    ) == yaml.safe_load((proj_path / "dvc.yaml").read_text())
    assert (CWD / "params_config" / "dataclass_w_deps_params_path.yaml").read_text() == (
        proj_path / "params.yaml"
    ).read_text()


if __name__ == "__main__":
    from pathlib import Path

    test_node_with_dc_model_params_deps(Path.cwd())
