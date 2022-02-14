from zntrack.core.parameter import ZnTrackOption
from zntrack.utils.lazy_loader import LazyOption


class ExampleClass:
    lazy_option = ZnTrackOption()


def test_lazy_load():
    lazy_obj = ExampleClass.lazy_option

    example_class = ExampleClass()
    lazy_obj.load(instance=example_class, lazy=True)

    assert example_class.__dict__["lazy_option"] is LazyOption

    assert example_class.lazy_option is not LazyOption
