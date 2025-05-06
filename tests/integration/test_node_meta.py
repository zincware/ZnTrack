import zntrack
from pathlib import Path
import pytest

class ReadFileContent(zntrack.Node):
    deps_file: Path = zntrack.deps_path()
    params: str = zntrack.params()

    def run(self):
        pass

@pytest.fixture()
def lockfile_01():
    return   {'cmd': 'zntrack run test_node_meta.ReadFileContent --name ReadFileContent',
   'deps': [{'hash': 'md5',
             'md5': '6dbd01b4309de2c22b027eb35a3ce18b',
             'path': 'data.txt',
             'size': 11}],
   'params': {'params.yaml': {'ReadFileContent': {'params': 'test'}}}}

def test_node_meta_lock(proj_path, lockfile_01):
    project = zntrack.Project()

    file = Path("data.txt")
    file.write_text("Lorem Ipsum")

    with project:
        _ = ReadFileContent(deps_file=file, params="test")
        
    project.repro()
    # TODO: do we want the node to requrie from_rev()? to update lockfile and other node-meta states?
    node = ReadFileContent.from_rev()
    assert node.state.lockfile == lockfile_01
        