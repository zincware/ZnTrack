import json
import pathlib

import yaml

import zntrack
import zntrack.examples
import zntrack.group

CWD = pathlib.Path(__file__).parent.resolve()


def test_apply(proj_path) -> None:
    project = zntrack.Project()

    JoinedParamsToOuts = zntrack.apply(zntrack.examples.ParamsToOuts, "join")  # noqa N806

    with project:
        zntrack.examples.ParamsToOuts(params=["a", "b"])
        JoinedParamsToOuts(params=["a", "b"])
        zntrack.apply(zntrack.examples.ParamsToOuts, "join")(params=["a", "b", "c"])

    project.build()

    assert json.loads((CWD / "zntrack_config" / "apply.json").read_text()) == json.loads(
        (proj_path / "zntrack.json").read_text()
    )
    assert yaml.safe_load(
        (CWD / "dvc_config" / "apply.yaml").read_text()
    ) == yaml.safe_load((proj_path / "dvc.yaml").read_text())
    assert (CWD / "params_config" / "apply.yaml").read_text() == (
        proj_path / "params.yaml"
    ).read_text()


if __name__ == "__main__":
    test_apply("")
