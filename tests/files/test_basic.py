import zntrack
import pathlib

class MyNode(zntrack.Node):
    parameter: int = zntrack.params()

CWD = pathlib.Path(__file__).parent.resolve()

def test_basic(proj_path):
    with zntrack.Project() as project:
        _ = MyNode(parameter=1)
    
    project.build()

    assert (CWD / "zntrack_config" / "basic.json").read_text() == (proj_path / "zntrack.json").read_text()
    assert (CWD / "dvc_config" / "basic.yaml").read_text() == (proj_path / "dvc.yaml").read_text()
    assert (CWD / "params_config" / "basic.yaml").read_text() == (proj_path / "params.yaml").read_text()
