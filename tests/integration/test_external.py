import pytest

import zntrack


class ExternalToOutput(zntrack.Node):
    node: zntrack.Node = zntrack.deps()
    outs = zntrack.outs()
    attr: str = zntrack.params()
    attr_is_func: bool = zntrack.params(False)

    def run(self):
        if self.attr_is_func:
            self.outs = getattr(self.node, self.attr)()
        else:
            self.outs = getattr(self.node, self.attr)


@pytest.mark.needs_internet
def test_external(proj_path):
    node = zntrack.from_rev(
        "HelloWorld",
        remote="https://github.com/PythonFZ/ZnTrackExamples.git",
        rev="fbb6ada",
    )

    with zntrack.Project() as proj:
        node = ExternalToOutput(node=node, attr="random_number")

    proj.run()
    node.load()
    assert node.outs == 123


@pytest.mark.needs_internet
def test_external_grp(proj_path):
    node = zntrack.from_rev(
        "HelloWorld",
        remote="https://github.com/PythonFZ/ZnTrackExamples.git",
        rev="fbb6ada",
    )

    proj = zntrack.Project()
    with proj.group("test"):
        node = ExternalToOutput(node=node, attr="random_number")

    proj.run()
    node.load()
    assert node.outs == 123
