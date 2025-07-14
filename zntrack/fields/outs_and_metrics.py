import json
import pathlib
import typing as t

import znjson

from zntrack import config
from zntrack.config import NOT_AVAILABLE, FieldTypes
from zntrack.fields.base import field
from zntrack.node import Node


def _outs_getter(self: "Node", name: str, suffix: str):
    # Use relative path if using DVCFileSystem
    if hasattr(self.state.fs, "repo") and self.state.fs.repo:
        # For DVCFileSystem, use path relative to repo root
        repo_root = pathlib.Path(self.state.fs.repo.root_dir)
        # nwd is already relative to the state.path, so we need to make it
        # relative to repo root
        nwd_path = self.nwd
        if nwd_path.is_absolute():
            try:
                relative_nwd = nwd_path.relative_to(repo_root)
                outs_path = str((relative_nwd / name).with_suffix(suffix))
            except ValueError:
                # If path is not relative to repo root, use absolute path
                outs_path = str((nwd_path / name).with_suffix(suffix))
        else:
            # nwd is already relative
            outs_path = str((nwd_path / name).with_suffix(suffix))
    else:
        # For local filesystem, use absolute path
        outs_path = (self.nwd / name).with_suffix(suffix)

    with self.state.fs.open(outs_path) as f:
        return json.load(f, cls=znjson.ZnDecoder)


def _outs_save_func(self: "Node", name: str, suffix: str):
    self.nwd.mkdir(parents=True, exist_ok=True)
    try:
        (self.nwd / name).with_suffix(suffix).write_text(
            znjson.dumps(getattr(self, name))
        )
    except TypeError as err:
        raise TypeError(f"Error while saving {name} to {self.nwd / name}.json") from err


def _metrics_save_func(self: "Node", name: str, suffix: str):
    self.nwd.mkdir(parents=True, exist_ok=True)
    try:
        (self.nwd / name).with_suffix(suffix).write_text(json.dumps(getattr(self, name)))
    except TypeError as err:
        raise TypeError(f"Error while saving {name} to {self.nwd / name}.json") from err


def outs(*, cache: bool = True, independent: bool = False, **kwargs) -> t.Any:
    """Define output for a node.

    An output can be anything that can be pickled.

    Parameters
    ----------
    cache : bool, optional
       Set to true to use the DVC cache for the field.
       Default is ``zntrack.config.ALWAYS_CACHE``.
    independent : bool, optional
         Whether the output is independent of the node's inputs. Default is `False`.

    Examples
    --------
    >>> import zntrack
    >>> class MyNode(zntrack.Node):
    ...     outs: int = zntrack.outs()
    ...
    ...     def run(self) -> None:
    ...         '''Save output to self.outs.'''
    """
    return field(
        default=NOT_AVAILABLE,
        cache=cache,
        independent=independent,
        field_type=FieldTypes.OUTS,
        dump_fn=_outs_save_func,
        suffix=".json",
        load_fn=_outs_getter,
        repr=False,
        init=False,
        **kwargs,
    )


def metrics(*, cache: bool | None = None, independent: bool = False, **kwargs) -> t.Any:
    """Define metrics for a node.

    The metrics must be a dictionary that can be serialized to JSON.

    Parameters
    ----------
    cache : bool, optional
       Set to true to use the DVC cache for the field.
       Default is ``zntrack.config.ALWAYS_CACHE``.
    independent : bool, optional
         Whether the output is independent of the node's inputs. Default is `False`.

    Examples
    --------
    >>> import zntrack
    >>> class MyNode(zntrack.Node):
    ...     metrics: dict = zntrack.metrics()
    ...
    ...     def run(self) -> None:
    ...         '''Save metrics to self.metrics.'''
    """
    if cache is None:
        cache = config.ALWAYS_CACHE
    return field(
        default=NOT_AVAILABLE,
        cache=cache,
        independent=independent,
        field_type=FieldTypes.METRICS,
        dump_fn=_metrics_save_func,
        suffix=".json",
        load_fn=_outs_getter,
        repr=False,
        init=False,
        **kwargs,
    )
