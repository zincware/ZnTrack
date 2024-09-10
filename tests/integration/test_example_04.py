import zntrack


class HelloWorld(zntrack.Node):
    """BasicTest class"""

    inputs: int = zntrack.params()
    output: int = zntrack.outs()

    def run(self):
        """Run method of the Node test instance"""
        self.output = self.inputs


def test_basic_io_assertion(proj_path):
    """Make a simple input/output assertion test for the nodes with different names"""
    project = zntrack.Project()
    with project:
        HelloWorld(inputs=3)
        HelloWorld(name="Test01", inputs=17)
        HelloWorld(name="Test02", inputs=42)

    project.run()

    assert HelloWorld.from_rev().output == 3
    assert HelloWorld.from_rev(name="Test01").output == 17
    assert HelloWorld.from_rev(name="Test02").output == 42
