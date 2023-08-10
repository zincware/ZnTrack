import git

import zntrack.examples


def test_patch_open(proj_path):
    with zntrack.Project() as proj:
        node = zntrack.examples.WriteDVCOuts(params="Hello World")

    proj.run()

    repo = git.Repo()

    repo.git.add(A=True)
    commit = repo.index.commit("initial commit")

    node.params = "Lorem Ipsum"
    proj.run()

    node = zntrack.examples.WriteDVCOuts.from_rev(rev=commit.hexsha)

    with node.state.patch_open():
        with open(node.outs, "r") as f:
            assert f.read() == "Hello World"

    with open(node.outs, "r") as f:
        assert f.read() == "Lorem Ipsum"
