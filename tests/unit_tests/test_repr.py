import zntrack.examples


class NodeWithPostInit(zntrack.Node):
    def __post_init__(self):
        # The parent implements a __post_init__ method
        # this tests if super().__post_init__ is called correctly
        super().__post_init__()


def test_repr(proj_path):
    assert (
        repr(zntrack.examples.ParamsToOuts(params=42))
        == "ParamsToOuts(name='ParamsToOuts', params=42)"
    )
    assert repr(zntrack.examples.WriteDVCOuts(params=42)) == (
        "WriteDVCOuts(name='WriteDVCOuts', params=42,"
        " outs=PosixPath('nodes/WriteDVCOuts/output.txt'))"
    )
    assert repr(NodeWithPostInit()) == "NodeWithPostInit(name='NodeWithPostInit')"
    assert repr(zntrack.Node()) == "Node(name='Node')"
    assert repr(zntrack.Node(name="SomeNode")) == "Node(name='SomeNode')"
    assert (
        repr(zntrack.examples.ParamsToMetrics(params=42))
        == "ParamsToMetrics(name='ParamsToMetrics', params=42)"
    )
    assert (
        repr(zntrack.examples.WritePlots())
        == "WritePlots(name='WritePlots', x=[1, 2, 3], y=[4, 5, 6])"
    )


def test_repr_from_rev(proj_path):
    with zntrack.Project() as proj:
        n1 = zntrack.examples.ParamsToOuts(params=42)
        n2 = zntrack.examples.WriteDVCOuts(params=42)
        n6 = zntrack.examples.ParamsToMetrics(params=42)
        n7 = zntrack.examples.WritePlots()

    proj.build()

    assert repr(n1) == "ParamsToOuts(name='ParamsToOuts', params=42)"
    assert repr(n2) == (
        "WriteDVCOuts(name='WriteDVCOuts',"
        " params=42, outs=PosixPath('nodes/WriteDVCOuts/output.txt'))"
    )

    assert repr(n6) == "ParamsToMetrics(name='ParamsToMetrics', params=42)"
    assert repr(n7) == "WritePlots(name='WritePlots', x=[1, 2, 3], y=[4, 5, 6])"

    proj.run()

    assert repr(n1) == "ParamsToOuts(name='ParamsToOuts', params=42)"
    assert repr(n2) == (
        "WriteDVCOuts(name='WriteDVCOuts', params=42,"
        " outs=PosixPath('nodes/WriteDVCOuts/output.txt'))"
    )

    assert repr(n6) == "ParamsToMetrics(name='ParamsToMetrics', params=42)"
    assert repr(n7) == "WritePlots(name='WritePlots', x=[1, 2, 3], y=[4, 5, 6])"
