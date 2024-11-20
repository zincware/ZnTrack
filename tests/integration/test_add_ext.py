import pytest

import zntrack.examples

apache_license = (
    "https://raw.githubusercontent.com/PythonFZ/zntrack-examples/refs/heads/main/LICENSE"
)

epl_license = "https://raw.githubusercontent.com/zincware/ZnDraw/refs/heads/main/LICENSE"


@pytest.mark.needs_internet
def test_add_read_url(proj_path) -> None:
    project = zntrack.Project()
    file = zntrack.add(apache_license, "LICENSE")

    with project:
        node_1 = zntrack.examples.ReadFile(path=file)
        node_2 = zntrack.examples.ReadFile(path=file)

    project.repro()

    assert "Apache License" in node_1.content
    assert "Apache License" in node_2.content

    project.repro()  # test run and build again


@pytest.mark.needs_internet
def test_add_two_files(proj_path) -> None:
    project = zntrack.Project()
    file_1 = zntrack.add(apache_license, "L1")
    file_2 = zntrack.add(apache_license, "L2")

    with project:
        node_1 = zntrack.examples.ReadFile(path=file_1)
        node_2 = zntrack.examples.ReadFile(path=file_2)

    project.repro()

    assert "Apache License" in node_1.content
    assert "Apache License" in node_2.content

    project.repro()  # test run and build again


@pytest.mark.needs_internet
def test_update_file(proj_path) -> None:
    project = zntrack.Project()
    file = zntrack.add(apache_license, "LICENSE")

    with project:
        node = zntrack.examples.ReadFile(path=file)

    project.repro()

    assert "Apache License" in node.content

    # new Project / rerunning

    project = zntrack.Project()
    file = zntrack.add(epl_license, "LICENSE", force=True)
    with project:
        node = zntrack.examples.ReadFile(path=file)

    project.repro()
    # TODO: can not use node.content because it seems to be read during building!

    assert "Eclipse Public License" in zntrack.from_rev(name=node.name).content

    project.repro()
