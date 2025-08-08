import zntrack
import dataclasses

@dataclasses.dataclass
class DCWithFn:
    value: int

    def get_number(self) -> int:
        return self.value

class NodeWithFn(zntrack.Node):
    """A node that uses auto-inferred fields with a function"""
    value: int

    def run(self):
        pass

    def get_number(self) -> int:
        return self.value

class NodeUsingFn(zntrack.Node):
    """A node that uses another node's function"""
    fn: NodeWithFn | DCWithFn
    result: int = zntrack.outs()

    def run(self):
        self.result = self.fn.get_number()

def test_auto_fields_with_function(proj_path):
    project = zntrack.Project()

    dc = DCWithFn(value=42)
    with project:
        n1 = NodeWithFn(value=10)
    with project.group("function"):
        t1 = NodeUsingFn(fn=n1)
        t2 = NodeUsingFn(fn=dc)
    
    project.repro()

    assert zntrack.from_rev(t1.name).result == 10
    assert zntrack.from_rev(t2.name).result == 42
