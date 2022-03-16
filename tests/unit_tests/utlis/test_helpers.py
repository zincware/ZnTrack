import pytest

from zntrack import Node
from zntrack.utils import helpers


class MyNode(Node):
    def run(self):
        pass


@pytest.mark.parametrize(
    ("node", "true_val"),
    [
        (MyNode(), True),
        (MyNode, True),
        ([MyNode, MyNode], True),
        ([MyNode(), MyNode()], True),
        ("Node", False),
        (["Node", MyNode()], True),
    ],
)
def test_isnode(node, true_val):
    assert helpers.isnode(node) == true_val
