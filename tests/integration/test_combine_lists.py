import zntrack

class GenerateList(zntrack.Node):
    size = zntrack.zn.params(10)
    outs = zntrack.zn.outs()

    def run(self):
        self.outs = list(range(self.size))

class AddOneToList(zntrack.Node):
    data = zntrack.zn.deps()
    outs = zntrack.zn.outs()

    def run(self) -> None:
        self.outs = [x + 1 for x in self.data]

def test_combine(proj_path):
    with zntrack.Project() as proj:
        a = GenerateList(size=1)
        b = GenerateList(size=2)
        c = GenerateList(size=3)

        added = AddOneToList(data=a.outs + b.outs + c.outs)

    proj.run(eager=True, save=False)

    assert added.outs == [1] + [1, 2] + [1, 2, 3]
