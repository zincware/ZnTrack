import pytest

from zntrack import zn
from zntrack.core import ZnTrackOption


def test_zn_outs_error():
    with pytest.raises(ValueError):

        class ExampleOutsDefault:
            node_name = "test"
            parameter = zn.outs(default="Lorem Ipsum")


def test_dvc_option_from_cls_name():
    with pytest.raises(ValueError):

        class CustomOption(ZnTrackOption):
            # CustomOption is not available in utils.DVCOption, therefore it does not work
            pass

        CustomOption()

    class params(ZnTrackOption):
        # Params is available
        pass

    params()

    class CustomOptions(ZnTrackOption):
        dvc_option = ""
        # defining a custom dvc_option works as well
        pass

    CustomOptions()


class CustomZnTrackOption(ZnTrackOption):
    dvc_option = ""

    def get_data_from_files(self, instance):
        return "Lorem Ipsum"


class ExampleParams:
    node_name = "test"
    is_loaded = True  # here we want to test the load from file
    parameter = CustomZnTrackOption()


class ExampleParamsDefault:
    node_name = "test"
    is_loaded = False  # here we test load from default
    parameter = zn.params(default="Lorem Ipsum")


@pytest.mark.parametrize("cls", [ExampleParams, ExampleParamsDefault])
def test_ExampleParamsDefault(cls):
    obj = cls()
    with pytest.raises(KeyError):
        _ = obj.__dict__["parameter"]
    assert obj.parameter == "Lorem Ipsum"
    assert obj.__dict__["parameter"] == "Lorem Ipsum"


class ExampleNode:
    method = zn.Method()


def test_method_filename():
    assert ExampleNode.method.get_filename(ExampleNode()) is None
