"""Test passing callables as dependencies instead of properties or attributes."""

import contextlib
import typing as t

import zntrack

ContextManagerGenInt = t.Generator[int, None, None]


class NodeWithFunction(zntrack.Node):
    parameter: int = zntrack.params()

    def get_parameter(self) -> int:
        return self.parameter

    def run(self) -> None:
        pass


class NodeWithContextManager(zntrack.Node):
    parameter: int = zntrack.params()

    @contextlib.contextmanager
    def get_parameter(self) -> ContextManagerGenInt:
        yield self.parameter

    def run(self) -> None:
        pass


class NodeWithFunctionDeps(zntrack.Node):
    fn: t.Callable[[], int] = zntrack.deps()
    result: int = zntrack.outs()

    def run(self) -> None:
        self.result = self.fn()


class NodeWithContextManagerDeps(zntrack.Node):
    cm: t.Callable[[], t.ContextManager[int]] = zntrack.deps()
    result: int = zntrack.outs()

    def run(self) -> None:
        with self.cm() as value:
            self.result = value


def test_node_with_function(proj_path):
    project = zntrack.Project()

    with project:
        a = NodeWithFunction(parameter=1)
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
