from zntrack import zn


class ExampleClass:
    module = None  # must mock the module here
    method = zn.Method()


def test_zn_method_get():
    class ExampleMethod:
        pass

    example = ExampleClass()
    example.method = ExampleMethod()

    assert isinstance(example.__dict__["method"], ExampleMethod)
    assert example.method.znjson_zn_method

    assert isinstance(ExampleClass.method.__get__(None, None), zn.Method)
