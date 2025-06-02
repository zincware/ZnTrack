from pathlib import Path

import zntrack.examples


def test_outs_path_to_deps_path(proj_path):
    (proj_path / "output.txt").write_text("15")

    with zntrack.Project() as proj:
        a = zntrack.examples.WriteDVCOuts(params=10)
        b = zntrack.examples.ReadFile(path=a.outs)
        #
        c = zntrack.examples.ReadFile(path=Path("output.txt"))

    proj.repro()

    assert a.outs == Path("nodes/WriteDVCOuts/output.txt")
    assert b.path == Path("nodes/WriteDVCOuts/output.txt")
    assert b.content == "10"
    # control
    assert c.path == Path("output.txt")
    assert c.content == "15"
