import pytest
import znflow

import zntrack


class CreateList(zntrack.Node):
    size: int = zntrack.params(10)

    output: list = zntrack.outs()

    def run(self):
        self.output = list(range(self.size))


class AddList(zntrack.Node):
    a: list = zntrack.deps()
    b: list = zntrack.deps()

    output: list = zntrack.outs()

    def run(self):
        self.output = self.a + self.b


@pytest.mark.parametrize("eager", [True, False])
def test_AddList(proj_path, eager):
    with zntrack.Project() as project:
        create_list_a = CreateList(name="CreateListA")
        create_list_b = CreateList(name="CreateListB")
        add_list = AddList(a=create_list_a.output, b=create_list_b.output)

    assert isinstance(add_list.a, znflow.Connection)
    assert isinstance(add_list.b, znflow.Connection)

    assert add_list.a.instance == create_list_a
    assert add_list.b.instance == create_list_b

    assert add_list.a.attribute == "output"
    assert add_list.b.attribute == "output"

    if eager:
        project.run()
    else:
        project.repro(build=True)

    assert create_list_a.output == list(range(10))
    assert create_list_b.output == list(range(10))
    assert add_list.output == list(range(10)) + list(range(10))


@pytest.mark.parametrize("eager", [True, False])
def test_AddList_getitem(proj_path, eager):
    with zntrack.Project() as project:
        create_list_a = CreateList(name="CreateListA")
        create_list_b = CreateList(name="CreateListB")
        add_list = AddList(a=create_list_a.output[1], b=create_list_b.output[-1])

    if eager:
        project.run()

        assert create_list_a.output == list(range(10))
        assert create_list_b.output == list(range(10))
        assert add_list.output == 10  # 1 + 9
    else:
        with pytest.raises(NotImplementedError):
            project.repro(build=True)


@pytest.mark.parametrize("eager", [True, False])
def test_AddList_slice(proj_path, eager):
    with zntrack.Project() as project:
        create_list_a = CreateList(name="CreateListA")
        create_list_b = CreateList(name="CreateListB")
        add_list = AddList(a=create_list_a.output[::2], b=create_list_b.output[2:7])

    if eager:
        project.run()

        assert create_list_a.output == list(range(10))
        assert create_list_b.output == list(range(10))
        assert add_list.output == list(range(10))[::2] + list(range(10))[2:7]
    else:
        with pytest.raises(NotImplementedError):
            project.repro(build=True)
