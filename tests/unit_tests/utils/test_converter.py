import json

import pytest
import znjson


@pytest.mark.parametrize("myslice", [slice(1, 2, 3), slice(1, 2), slice(1)])
def test_slice_converter(myslice):
    dump = json.dumps(myslice, cls=znjson.ZnEncoder)
    assert json.loads(dump, cls=znjson.ZnDecoder) == myslice
