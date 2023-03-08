import json
import pathlib

import numpy as np
import pytest

from zntrack import Node, zn


class SingleNode(Node):
    param1 = zn.params()

    def run(self):
        pass


@pytest.mark.parametrize("value", [np.arange(4), pathlib.Path("test.txt")])
def test_unsupported_params(proj_path, value):
    """Check that unsupported params raise an error."""
    node = SingleNode(param1=value)
    with pytest.raises(TypeError):
        node.save()
