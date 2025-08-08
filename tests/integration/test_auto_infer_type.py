import dataclasses

import zntrack
import pytest


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
        n1 = NodeWithFn(value=10) # value is params
    with project.group("function"):
        t1 = NodeUsingFn(fn=n1) # fn is deps
        t2 = NodeUsingFn(fn=dc) # fn is deps
    
    with project.group("deps"):
        n2 = NodeWithFn(value=t1.result) # value is deps

    project.repro()

    assert zntrack.from_rev(t1.name).result == 10
    assert zntrack.from_rev(t2.name).result == 42
    assert zntrack.from_rev(n2.name).value == 10

def test_mixed_auto_fields(proj_path):
    project = zntrack.Project()
    dc = DCWithFn(value=42)
    with project:
        t1 = NodeUsingFn(fn=[1, dc]) # type: ignore
        # needs to raise an error, because can't be both params and deps
    with pytest.raises(ValueError):
        #  ValueError: Found unsupported type '<class 'int'>' (1) for DEPS field 'fn' in list
        project.build()
