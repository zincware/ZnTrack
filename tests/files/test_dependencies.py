import zntrack

class NodeA(zntrack.Node):

    def run(self):
        pass

class NodeB(zntrack.Node):
    input: NodeA = zntrack.deps()

    def run(self):
        pass


def test_deps(proj_path):
    with zntrack.Project() as project:
        a = NodeA()
        b = NodeB(input=a)

    project.build()
