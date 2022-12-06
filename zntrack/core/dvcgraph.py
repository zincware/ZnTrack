"""DVC Graph as parent class for the Node."""
from __future__ import annotations

import dataclasses
import logging
import pathlib
import typing

from zninit.descriptor import DescriptorTypeT, get_descriptors

from zntrack import utils
from zntrack.core.zntrackoption import ZnTrackOption

log = logging.getLogger(__name__)


@dataclasses.dataclass
class DVCRunOptions:
    """Collection of DVC run options.

    Attributes
    ----------
    All attributes are documented under the dvc run method.

    References
    ----------
    https://dvc.org/doc/command-reference/run#options
    """

    no_commit: bool
    external: bool
    always_changed: bool
    no_run_cache: bool
    force: bool

    @property
    def dvc_args(self) -> list:
        """Get the activated options.

        Returns
        -------
        list: A list of strings for the subprocess call, e.g.:
            ["--no-commit", "--external"]
        """
        out = []
        for datacls_field in dataclasses.fields(self):
            value = getattr(self, datacls_field.name)
            if value:
                out.append(f"--{datacls_field.name.replace('_', '-')}")
        return out


def handle_dvc(value, dvc_args) -> list:
    """Convert list of dvc_paths to a dvc input string.

    >>> handle_dvc("src/file.txt", "outs") == ["--outs", "src/file.txt"]
    """
    if not isinstance(value, (list, tuple)):
        value = [value]

    def option_func(_dvc_path):
        return f"--{dvc_args}"

    def posix_func(dvc_path):
        if dvc_args == "params":
            # add :to the end to indicate that it actually is a file.
            try:
                return f"{pathlib.Path(dvc_path).as_posix()}:"
            except TypeError as err:
                raise ValueError(
                    f"dvc.params does not support type {type(dvc_path)}"
                ) from err
        return pathlib.Path(dvc_path).as_posix()

    # double list comprehension https://stackoverflow.com/a/11869360/10504481
    return [f(x) for x in value for f in (option_func, posix_func)]


def filter_ZnTrackOption(
    data,
    cls,
    zn_type: typing.Union[utils.ZnTypes, typing.List[utils.ZnTypes]],
    return_with_type=False,
    allow_none: bool = False,
) -> dict:
    """Filter the descriptor instances by zn_type.

    Parameters
    ----------
    data: List[ZnTrackOption]
        The ZnTrack options to query through
    cls:
        The instance the ZnTrack options are attached to
    zn_type: str
        The zn_type of the descriptors to gather
    return_with_type: bool, default=False
        return a dictionary with the Descriptor.dvc_option as keys
    allow_none: bool, default=False
        Use getattr(obj, name, None) instead of getattr(obj, name) to yield
        None when an AttributeError occurs.

    Returns
    -------
    dict:
        either {attr_name: attr_value}
        or
        {descriptor.dvc_option: {attr_name: attr_value}}

    """
    if not isinstance(zn_type, (list, tuple)):
        zn_type = (zn_type,)
    data = [x for x in data if x.zn_type in zn_type]
    if return_with_type:
        types_dict = {x.dvc_option: {} for x in data}
        for entity in data:
            if allow_none:
                # avoid AttributeError
                value = getattr(cls, entity.name, None)
            else:
                value = getattr(cls, entity.name)
            types_dict[entity.dvc_option].update({entity.name: value})
        return types_dict
    output = {}
    for attr in data:
        try:
            output[attr.name] = getattr(cls, attr.name)
        except utils.exceptions.DataNotAvailableError as err:
            if allow_none:
                output[attr.name] = None
            else:
                raise err
    return output


def prepare_dvc_script(
    node_name,
    dvc_run_option: DVCRunOptions,
    custom_args: list,
    nb_name,
    module,
    func_or_cls,
    call_args,
) -> list:
    """Prepare the dvc cmd to be called by subprocess.

    Parameters
    ----------
    node_name: str
        Name of the Node
    dvc_run_option: DVCRunOptions
        dataclass to collect special DVC run options
    custom_args: list[str]
        all the params / deps / ... to be added to the script
    nb_name: str|None
        Notebook name for jupyter support
    module: str
        like "src.my_module"
    func_or_cls: str
        The name of the Node class or function to be imported and run
    call_args: str
        Additional str like "(run_func=True)" or ".load().run_and_save"

    Returns
    -------
    list[str]
        The list to be passed to the subprocess call
    """
    script = ["stage", "add", "-n", node_name]
    script += dvc_run_option.dvc_args
    script += custom_args

    if nb_name is not None:
        script += ["--deps", utils.module_to_path(module).as_posix()]

    import_str = f"""{utils.config.interpreter} -c "from {module} import """
    import_str += f"""{func_or_cls}; {func_or_cls}{call_args}" """
    script += [import_str]
    log.debug(f"dvc script: {' '.join([str(x) for x in script])}")
    return script


class ZnTrackInfo:
    """Helping class for access to ZnTrack information."""

    def __init__(self, parent):
        """ZnTrackInfo __init__."""
        self._parent = parent

    def __repr__(self) -> str:
        """__repr__."""
        return f"ZnTrackInfo: {self._parent}"

    def collect(
        self, zntrackoption: typing.Type[DescriptorTypeT] = ZnTrackOption
    ) -> dict:
        """Collect the values of all ZnTrackOptions of the passed type.

        Parameters
        ----------
        zntrackoption:
            Any cls of a ZnTrackOption such as zn.params.
            By default, collect all ZnTrackOptions

        Returns
        -------
        dict:
            A dictionary of {option_name: option_value} for all found options of
            the given type zntrackoption.
        """
        if isinstance(zntrackoption, (list, tuple)):
            raise ValueError(
                "collect only supports single ZnTrackOptions. Found"
                f" {zntrackoption} instead."
            )
        options = get_descriptors(zntrackoption, self=self._parent)
        return {x.name: x.__get__(self._parent) for x in options}


def run_post_dvc_cmd(descriptor_list, instance):
    """Run all post-dvc-cmds like plots modify."""
    for desc in descriptor_list:
        if desc.post_dvc_cmd(instance) is not None:
            utils.run_dvc_cmd(desc.post_dvc_cmd(instance))
