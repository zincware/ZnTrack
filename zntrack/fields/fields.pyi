import os
from typing import Any, Callable, Optional, TypeVar, Union, overload

from zninit.descriptor import Empty

_T = TypeVar("_T")
_P = TypeVar("_P", bound=Union[str, bytes, os.PathLike])

def outs() -> Any: ...

# TODO: metricts
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

# TODO: deps
# TODO: plots
@overload
def outs_path(dvc_option: str = ..., **kwargs) -> Any: ...
@overload
def outs_path(args: _P, dvc_option: str = ..., **kwargs) -> _P: ...
@overload
def outs_path(arg1: _P, *args: _P, dvc_option: str = ..., **kwargs) -> tuple[_P, ...]: ...
@overload
def metrics_path(dvc_option: str = ..., **kwargs) -> Any: ...
@overload
def metrics_path(args: _P, dvc_option: str = ..., **kwargs) -> _P: ...
@overload
def metrics_path(
    arg1: _P, *args: _P, dvc_option: str = ..., **kwargs
) -> tuple[_P, ...]: ...
@overload
def params_path(**kwargs) -> Any: ...
@overload
def params_path(args: _P, **kwargs) -> _P: ...
@overload
def params_path(arg1: _P, *args: _P, **kwargs) -> tuple[_P, ...]: ...
@overload
def deps_path(**kwargs) -> Any: ...
@overload
def deps_path(args: _P, **kwargs) -> _P: ...
@overload
def deps_path(arg1: _P, *args: _P, **kwargs) -> tuple[_P, ...]: ...
@overload
def plots_path(dvc_option: str = ..., **kwargs) -> Any: ...
@overload
def plots_path(args: _P, dvc_option: str = ..., **kwargs) -> _P: ...
@overload
def plots_path(
    arg1: _P, *args: _P, dvc_option: str = ..., **kwargs
) -> tuple[_P, ...]: ...
