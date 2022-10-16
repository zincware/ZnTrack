import typing

from zntrack import Node, zn


# Test basic functionality of a single Node
class InputOutput(Node):
    input = zn.params()
    output = zn.outs()

    def run(self):
        self.output = self.input


def test_InputOutput_write_graph(proj_path, benchmark):
    benchmark(InputOutput(input=25).write_graph, dry_run=True)


def test_InputOutput_run_and_save(proj_path, benchmark):
    node = InputOutput(input=25)
    benchmark(node.run_and_save)


def test_InputOutput_load(proj_path, benchmark):
    InputOutput(input=25).write_graph(run=True)
    benchmark(InputOutput.load)


def test_InputOutput_load_lazy(proj_path, benchmark):
    InputOutput(input=25).write_graph(run=True)
    benchmark(InputOutput.load, lazy=True)


# Test Node-Node dependencies
class NodeCollector(Node):
    nodes: typing.List[InputOutput] = zn.deps()
    output = zn.outs()

    def run(self):
        self.output = sum(x.output for x in self.nodes)


def test_NodeCollector_write_graph(proj_path, benchmark):
    io_node_1 = InputOutput(input=10)
    io_node_1.write_graph()
    io_node_2 = InputOutput(input=20)
    io_node_2.write_graph()

    benchmark(NodeCollector(nodes=[io_node_1, io_node_2]).write_graph)


def test_NodeCollector_run_and_save(proj_path, benchmark):
    io_node_1 = InputOutput(input=10)
    io_node_1.write_graph(run=True)
    io_node_2 = InputOutput(input=20)
    io_node_2.write_graph(run=True)
    NodeCollector(nodes=[io_node_1, io_node_2]).write_graph()

    benchmark(NodeCollector.load().run_and_save)


def test_NodeCollector_load(proj_path, benchmark):
    io_node_1 = InputOutput(input=10)
    io_node_1.write_graph(run=True)
    io_node_2 = InputOutput(input=20)
    io_node_2.write_graph(run=True)
    NodeCollector(nodes=[io_node_1, io_node_2]).write_graph(run=True)
    benchmark(NodeCollector.load)


def test_NodeCollector_load_lazy(proj_path, benchmark):
    io_node_1 = InputOutput(input=10)
    io_node_1.write_graph(run=True)
    io_node_2 = InputOutput(input=20)
    io_node_2.write_graph(run=True)
    NodeCollector(nodes=[io_node_1, io_node_2]).write_graph(run=True)
    benchmark(NodeCollector.load, lazy=True)
