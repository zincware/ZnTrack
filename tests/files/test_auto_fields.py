import dataclasses
import json
import pathlib

import yaml

import zntrack
import zntrack.examples

CWD = pathlib.Path(__file__).parent.resolve()


class NodeWithAutoFields(zntrack.Node):
    """A node that uses auto-inferred fields"""

    value: int


class NodeWithAutoFieldsList(zntrack.Node):
    value: list


@dataclasses.dataclass
class SomeDataClass:
    """just to test passing a dataclass works"""

    x: int


def test_auto_fields_inference(proj_path):
    project = zntrack.Project()

    dc = SomeDataClass(x=42)
    with project:
        n1 = zntrack.examples.ParamsToOuts(params=16)
    with project.group("int"):
        t1 = NodeWithAutoFields(value=10)
        t2 = NodeWithAutoFields(value=n1.outs)
        t3 = NodeWithAutoFields(value=dc)  # type: ignore
    with project.group("list"):
        t4 = NodeWithAutoFieldsList(value=[1, 2, 3])
        t5 = NodeWithAutoFieldsList(value=[n1.outs])
        t6 = NodeWithAutoFieldsList(value=[dc])
    # with project.group("list-mixed"):  # these are currently not supported and should raise errors
    #     t7 = NodeWithAutoFieldsList(value=[1, 2, 3, n1.outs])
    #     t8 = NodeWithAutoFieldsList(value=[dc, 4, 5])
    #     t9 = NodeWithAutoFieldsList(value=[n1.outs, dc])
    #     t10 = NodeWithAutoFieldsList(value=[1, 2, dc, n1.outs])

    project.build()

    assert json.loads(
        (CWD / "zntrack_config" / "auto_fields.json").read_text()
    ) == json.loads((proj_path / "zntrack.json").read_text())
    assert yaml.safe_load(
        (CWD / "dvc_config" / "auto_fields.yaml").read_text()
    ) == yaml.safe_load((proj_path / "dvc.yaml").read_text())
    assert (CWD / "params_config" / "auto_fields.yaml").read_text() == (
        proj_path / "params.yaml"
    ).read_text()


if __name__ == "__main__":
    test_auto_fields_inference(None)
