import zntrack
import znflow


class NodeWithProperty(zntrack.Node):
    params = zntrack.zn.params(None)

    @property
    def calc(self):
        """This should not change the params if not called."""
        self.params = 42
        return "calc"

    def run(self):
        pass


def test_NodeWithProperty(proj_path):
    with zntrack.Project() as proj:
        node = NodeWithProperty()

    proj.run()

    node.load()
    assert node.params is None
