"""Test passing callables as dependencies instead of properties or attributes."""
import zntrack
import dataclasses
import contextlib
import typing as t

class NodeWithFunction(zntrack.Node):
    parameter: int = zntrack.params()

    def get_parameter(self):
        return self.parameter
    
    def run(self):
        pass

@dataclasses.dataclass
class ExNodeWithFunction:
    parameter: int 

    def get_parameter(self):
        return self.parameter
    

class NodeWithContextManager(zntrack.Node):
    parameter: int = zntrack.params()

    @contextlib.contextmanager
    def get_parameter(self) -> t.ContextManager[int]:
        yield self.parameter

    def run(self):
        pass

@dataclasses.dataclass
class ExNodeWithContextManager:
    parameter: int 

    @contextlib.contextmanager
    def get_parameter(self) -> t.ContextManager[int]:
        yield self.parameter


class NodeWithFunctionDeps(zntrack.Node):
    fn: t.Callable = zntrack.deps()
    result: int = zntrack.outs()

    def run(self):
        self.result = self.fn()

class NodeWithContextManagerDeps(zntrack.Node):
    cm: t.ContextManager[int] = zntrack.deps()
    result: int = zntrack.outs()

    def run(self):
        with self.cm() as value:
            self.result = value


def test_node_with_function(proj_path):
    project = zntrack.Project()

    with project:
        a = NodeWithFunction(parameter=1)
        b = NodeWithFunctionDeps(fn=a.get_parameter)

    project.repro()

    assert b.result == 1

def test_ext_node_with_function(proj_path):
    project = zntrack.Project()

    a = ExNodeWithFunction(parameter=1)
    with project:
        b = NodeWithFunctionDeps(fn=a.get_parameter)
    project.repro()
    assert b.result == 1

def test_node_with_context_manager(proj_path):
    project = zntrack.Project()

    with project:
        a = NodeWithContextManager(parameter=1)
        b = NodeWithContextManagerDeps(cm=a.get_parameter)

    project.repro()

    assert b.result == 1

def test_ext_node_with_context_manager(proj_path):
    project = zntrack.Project()

    a = ExNodeWithContextManager(parameter=1)
    with project:
        b = NodeWithContextManagerDeps(cm=a.get_parameter)
    project.repro()
    assert b.result == 1
