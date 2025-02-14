from zntrack import Node
from zntrack.examples.nodes import (
    AddNodeAttributes,
    AddNodeNumbers,
    AddNodes,
    AddNodes2,
    AddNumbers,
    AddNumbersProperty,
    AddOne,
    ComputeRandomNumber,
    ComputeRandomNumberNamed,
    ComputeRandomNumberWithParams,
    DepsToMetrics,
    NodeWithRestart,
    OptionalDeps,
    ParamsToMetrics,
    ParamsToOuts,
    ReadFile,
    SumNodeAttributes,
    SumNodeAttributesToMetrics,
    SumRandomNumbers,
    SumRandomNumbersNamed,
    WriteDVCOuts,
    WriteDVCOutsPath,
    WriteDVCOutsSequence,
    WriteMultipleDVCOuts,
    WritePlots,
)

__all__ = [
    "AddNumbers",
    "ReadFile",
    "ParamsToOuts",
    "ParamsToMetrics",
    "DepsToMetrics",
    "WritePlots",
    "AddNodeNumbers",
    "AddNumbersProperty",
    "AddNodes",
    "AddNodes2",
    "AddNodeAttributes",
    "AddNodeNumbers",
    "SumNodeAttributes",
    "SumNodeAttributesToMetrics",
    "AddOne",
    "WriteDVCOuts",
    "WriteDVCOutsSequence",
    "WriteDVCOutsPath",
    "WriteMultipleDVCOuts",
    "ComputeRandomNumber",
    "ComputeRandomNumberWithParams",
    "ComputeRandomNumberNamed",
    "SumRandomNumbers",
    "SumRandomNumbersNamed",
    "NodeWithRestart",
    "OptionalDeps",
]


def nodes() -> list[Node]:
    """Return the available nodes, grouped into categories."""

    return [globals()[name] for name in __all__]
