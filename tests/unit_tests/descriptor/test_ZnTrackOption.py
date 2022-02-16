from zntrack.core.parameter import ZnTrackOption
from zntrack.utils.lazy_loader import LazyOption


class ExampleClass:
    lazy_option = ZnTrackOption(lazy=True)
    node_name = ""  # required for ZnTrackOption to work


def test_lazy_load():
    lazy_obj = ExampleClass.lazy_option

    example_class = ExampleClass()
    lazy_obj.update_instance(instance=example_class, lazy=True)

    assert example_class.__dict__["lazy_option"] is LazyOption

    # TODO does not work because of missing metadata in ZnTrackOption
    # assert example_class.lazy_option is not LazyOption
