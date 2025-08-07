"""Test file to verify type annotations work correctly for zntrack fields.

This test should pass type checking with pyright/mypy.
The main goal is to ensure that patterns like:
    field: int = zntrack.params()
    field: str = zntrack.outs()
do not raise type errors when no explicit value is provided.
"""

import zntrack
from pathlib import Path


class TestFieldAnnotations(zntrack.Node):
    """Test basic field type annotations without explicit values."""
    
    # These should NOT raise type errors (the main fix)
    param_int: int = zntrack.params()
    param_str: str = zntrack.params()
    param_dict: dict = zntrack.params()
    
    out_int: int = zntrack.outs()
    out_str: str = zntrack.outs()
    out_dict: dict = zntrack.outs()
    
    metric_dict: dict = zntrack.metrics()
    
    dep_int: int = zntrack.deps()
    dep_str: str = zntrack.deps()
    
    plots_data = zntrack.plots()  # pandas.DataFrame, but we don't enforce the type
    
    # Path fields
    params_path_str: str = zntrack.params_path()
    params_path_path: Path = zntrack.params_path()
    outs_path_str: str = zntrack.outs_path()
    outs_path_path: Path = zntrack.outs_path()
    deps_path_str: str = zntrack.deps_path()
    deps_path_path: Path = zntrack.deps_path()
    plots_path_path: Path = zntrack.plots_path()
    metrics_path_path: Path = zntrack.metrics_path()

    def run(self):
        pass


class TestFieldAnnotationsWithDefaults(zntrack.Node):
    """Test that type safety is maintained when providing explicit values."""
    
    # These should work fine (correct type matching)
    param_good_int: int = zntrack.params(42)
    param_good_str: str = zntrack.params("hello")
    param_good_dict: dict = zntrack.params({})
    
    # Using default_factory
    param_factory: list = zntrack.params(default_factory=list)
    
    # Path fields with correct types
    params_path_str_with_val: str = zntrack.params_path("config.yaml")
    params_path_path_with_val: Path = zntrack.params_path(Path("config.yaml"))

    # Path fiels using zntrack.nwd
    outs_path_in_nwd: Path = zntrack.outs_path(zntrack.nwd / "output.txt")
    metrics_path_in_nwd: Path = zntrack.metrics_path(zntrack.nwd / "metrics.json")
    plots_path_in_nwd: Path = zntrack.plots_path(zntrack.nwd / "plot.png")

    # plots_path_list
    plots_path_list: list = zntrack.plots_path(default_factory = lambda: ["plot1.png", "plot2.png"])

    # path using tuples
    params_path_tuple: tuple[Path, ...] = zntrack.params_path((zntrack.nwd / "config1.yaml", zntrack.nwd / "config2.yaml"))
    outs_path_tuple: tuple[Path, ...] = zntrack.outs_path((zntrack.nwd / "output1.txt", zntrack.nwd / "output2.txt"))


    def run(self):
        pass

class TestTypeSafetyErrors(zntrack.Node):
    """These should cause type errors to ensure type safety is maintained.
    """
    
    # # Type mismatches with explicit values (should error when uncommented)
    param_bad_int: int = zntrack.params("string")  # Should error: str not assignable to int
    param_bad_str: str = zntrack.params(42)        # Should error: int not assignable to str
    param_bad_dict: dict = zntrack.params("not_a_dict")  # Should error: str not assignable to dict
    
    # # # Path field type mismatches (should error when uncommented)  
    params_path_bad: Path = zntrack.params_path(1234)  # Should error: int not assignable to path types
    outs_path_bad: str = zntrack.outs_path(42)  # Should error: int not assignable to path types
    deps_path_bad: Path = zntrack.deps_path(3.14)  # Should error: float not assignable to path types
    
    # List vs single type mismatches (should error when uncommented)
    outs_path_list_mismatch: str = zntrack.outs_path(["file1.txt", "file2.txt"])  # Should error: list not assignable to str
    params_path_list_mismatch: Path = zntrack.params_path(["config1.yaml", "config2.yaml"])  # Should error: list not assignable to Path
    # using default factory with list
    params_path_list_mismatch: Path = zntrack.params_path(default_factory= lambda: ["config1.yaml", "config2.yaml"])  # Should error: list not assignable to Path
    
    # Factory function returning wrong type (should error when uncommented)
    param_factory_bad: int = zntrack.params(default_factory=str)  # Should error: str() returns str, not int
    param_factory_bad2: dict = zntrack.params(default_factory=list)  # Should error: list() returns list, not dict

    # zntrack.nwd as string
    nwd_as_str: str = zntrack.outs_path(zntrack.nwd / "output.txt")  # Should error: str not assignable to Path

