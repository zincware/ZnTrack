import zntrack.examples
from pathlib import Path

def test_outs_path_to_deps_path(proj_path):
    with zntrack.Project() as proj:
        a = zntrack.examples.WriteDVCOuts(params=10)
        # assert a.outs == Path("nodes/WriteDVCOuts/output.txt") # uses znflow.resolve
        b = zntrack.examples.ReadFile(path=a.outs)
        # b = zntrack.examples.ReadFile(path=znflow.resolve(a.outs))
        # b = zntrack.examples.ReadFile(path=Path("nodes/WriteDVCOuts/output.txt")) # works

    proj.repro()

    assert a.outs == Path("nodes/WriteDVCOuts/output.txt")
    assert b.path == Path("nodes/WriteDVCOuts/output.txt")
    assert b.content == "10"