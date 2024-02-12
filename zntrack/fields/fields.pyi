from typing import Any, Callable, Optional, TypeVar, overload

from zninit.descriptor import Empty

_T = TypeVar("_T")

def outs() -> Any: ...

@overload
def params(
    default: Empty = ...,
    owner=...,
    instance=...,
    name=...,
    use_repr: bool = ...,
    repr_func: Callable = ...,
    check_types: bool = False,
    metadata: Optional[dict] = ...,
    frozen: bool = False,
    on_setattr: Optional[Callable] = ...,
) -> Any: ...

@overload
def params(
    default: _T,
    owner=...,
    instance=...,
    name=...,
    use_repr: bool = ...,
    repr_func: Callable = ...,
    check_types: bool = False,
    metadata: Optional[dict] = ...,
    frozen: bool = False,
    on_setattr: Optional[Callable] = ...,
) -> _T: ...
