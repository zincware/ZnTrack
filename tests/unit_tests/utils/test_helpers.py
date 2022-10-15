import pytest

from zntrack import Node
from zntrack.utils import helpers


class MyNode(Node):
    def run(self):
        pass


@pytest.mark.parametrize(
    ("node", "allow_subclass", "true_val"),
    [
        (MyNode(), True, True),
        (MyNode, True, True),
        (MyNode, False, False),
        ([MyNode, MyNode], True, True),
        ([MyNode(), MyNode()], True, True),
        ([MyNode(), MyNode], False, False),
        ("Node", True, False),
        (["Node", MyNode()], True, False),
        (
            [
                MyNode(),
                "Node",
            ],
            True,
            False,
        ),
        ([MyNode(), "Node", MyNode], False, False),
    ],
)
def test_isnode(node, allow_subclass, true_val):
    assert helpers.isnode(node, subclass=allow_subclass) == true_val
