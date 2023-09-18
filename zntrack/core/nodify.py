"""The @nodify decorator."""
import copy
import dataclasses
import json
import logging
import pathlib
import typing

import dot4dict
import znflow
import znjson

from zntrack.notebooks.jupyter import jupyter_class_to_file
from zntrack.utils import config, file_io, module_handler, run_dvc_cmd

log = logging.getLogger(__name__)

StrOrPath = typing.Union[str, pathlib.Path]

UnionListOrStrAndPath = typing.Union[typing.List[StrOrPath], StrOrPath]
UnionDictListOfStrPath = typing.Union[
    typing.List[StrOrPath], typing.Dict[str, StrOrPath], StrOrPath
]


@dataclasses.dataclass
class DVCRunOptions:
    """Collection of DVC run options.

    Attributes
    ----------
    All attributes are documented under the dvc run method.

    References
    ----------
    https://dvc.org/doc/command-reference/run#options.
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
            ["--no-commit", "--external"].
        """
        out = []
        for datacls_field in dataclasses.fields(self):
            value = getattr(self, datacls_field.name)
            if value:
                out.append(f"--{datacls_field.name.replace('_', '-')}")
        return out


def module_to_path(module: str, suffix=".py") -> pathlib.Path:
    """Convert module a.b.c to path(a/b/c)."""
    return pathlib.Path(*module.split(".")).with_suffix(suffix)


def prepare_dvc_script(
    node_name,
    dvc_run_option: DVCRunOptions,
    custom_args: list,
    nb_name,
    module,
    func_or_cls,
    call_args=None,
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
        The list to be passed to the subprocess call.
    """
    script = ["stage", "add", "-n", node_name]
    script += dvc_run_option.dvc_args
    script += custom_args

    if nb_name is not None:
        script += ["--deps", module_to_path(module).as_posix()]

    import_str = f"zntrack run {module}.{func_or_cls}"
    if call_args is not None:
        import_str += f" {call_args}"

    script += [import_str]
    log.debug(f"dvc script: {' '.join([str(x) for x in script])}")
    return script


def check_type(
    obj, types, allow_iterable=False, allow_none=False, allow_dict=False
) -> bool:
    """Check if the obj is of the given types.

    This includes recursive search for nested lists / dicts and fails
    if any of the values is not in types

    Parameters
    ----------
    obj:
        object to check
    types:
        single class or tuple of classes to check against
    allow_iterable:
        check list entries if a list is provided
    allow_none:
        accept None even if not in types.
    allow_dict:
        allow for {key: types}
    """
    if isinstance(obj, (list, tuple, set)) and allow_iterable:
        for value in obj:
            if check_type(value, types, allow_iterable, allow_none, allow_dict):
                continue
            return False
    elif isinstance(obj, dict) and allow_dict:
        for value in obj.values():
            if check_type(value, types, allow_iterable, allow_none, allow_dict):
                continue
            return False
    else:
        if allow_none and obj is None:
            return True
        if not isinstance(obj, types):
            return False

    return True


@dataclasses.dataclass
class NodeConfig:
    """DataClass to contain the arguments passed by the user.

    Attributes
    ----------
    All dvc attributes but connected by "_" instead of "-"

    """

    params: typing.Union[dot4dict.dotdict, dict] = dataclasses.field(default_factory=dict)
    outs: UnionDictListOfStrPath = None
    outs_no_cache: UnionDictListOfStrPath = None
    outs_persist: UnionDictListOfStrPath = None
    outs_persist_no_cache: UnionDictListOfStrPath = None
    metrics: UnionDictListOfStrPath = None
    metrics_no_cache: UnionDictListOfStrPath = None
    deps: UnionDictListOfStrPath = None
    plots: UnionDictListOfStrPath = None
    plots_no_cache: UnionDictListOfStrPath = None

    def __post_init__(self):
        """Dataclass post_init."""
        for datacls_field in dataclasses.fields(self):
            # type checking
            option_value = getattr(self, datacls_field.name)
            if datacls_field.name == "params":
                # params does not have to be a string
                if not isinstance(option_value, dict) and option_value is not None:
                    raise ValueError("Parameter must be dict or dot4dict.dotdict.")
            elif not check_type(
                option_value,
                (str, pathlib.Path),
                allow_iterable=True,
                allow_none=True,
                allow_dict=True,
            ):
                raise ValueError(
                    f"{option_value} is not a supported type. "
                    "Please use single values or lists of <str> and <pathlib.Path>."
                )

    def convert_fields_to_dotdict(self):
        """Update all fields to dotdict, if they are of type dict."""
        for datacls_field in dataclasses.fields(self):
            option_value = getattr(self, datacls_field.name)
            if isinstance(option_value, dict):
                setattr(self, datacls_field.name, dot4dict.dotdict(option_value))

    def write_dvc_command(self, node_name: str) -> list:
        """Collect dvc commands.

        Parameters
        ----------
        node_name:str
            name of the node, usually func.__name__

        Returns
        -------
        list: a list of all options like
        ["--outs", "outs.txt", "--params", "params.yaml:<node_name>", ...]
        handling lists of files as well the parameters

        """
        script = []
        if self.params is not None and len(self.params) > 0:
            script += ["--params", f"{config.files.params}:{node_name}"]
        for datacls_field in dataclasses.fields(self):
            if datacls_field.name == "params":
                continue
            if isinstance(getattr(self, datacls_field.name), (list, tuple)):
                for element in getattr(self, datacls_field.name):
                    script += [
                        f"--{datacls_field.name.replace('_', '-')}",
                        pathlib.Path(element).as_posix(),
                    ]
            elif isinstance(getattr(self, datacls_field.name), dict):
                for element in getattr(self, datacls_field.name).values():
                    script += [
                        f"--{datacls_field.name.replace('_', '-')}",
                        pathlib.Path(element).as_posix(),
                    ]
            elif getattr(self, datacls_field.name) is not None:
                script += [
                    f"--{datacls_field.name.replace('_', '-')}",
                    pathlib.Path(getattr(self, datacls_field.name)).as_posix(),
                ]

        return script


def save_node_config_to_files(cfg: NodeConfig, node_name: str):
    """Save the values from cfg to zntrack.json / params.yaml.

    Parameters
    ----------
    cfg: NodeConfig
        The NodeConfig object which should be serialized to zntrack.json / params.yaml
    node_name: str
        The name of the node, usually func.__name__.
    """
    for value_name, value in dataclasses.asdict(cfg).items():
        if value_name == "params":
            file_io.update_config_file(
                file=config.files.params,
                node_name=node_name,
                value_name=None,
                value=value,
            )
        else:
            file_io.update_config_file(
                file=pathlib.Path(config.files.zntrack),
                node_name=node_name,
                value_name=value_name,
                value=value,
            )


def decode_dict(value):
    """Decode dict that was loaded without znjson."""
    return json.loads(json.dumps(value), cls=znjson.ZnDecoder)


def execute_function_call(func):
    """Run the function call.

    1. Load the parameters from the Files.zntrack / Files.params
    2. Deserialize them
    3. Update the cfg: NodeConfig
    4. return the func(cfg)

    Parameters
    ----------
    func: callable
        decorated function

    Returns
    -------
    not used - return function return value

    """
    # TODO should exec_func always load from file or check if values
    #  are passed and then update the files?
    cfg_file_content = file_io.read_file(pathlib.Path(config.files.zntrack))[
        func.__name__
    ]
    cfg_file_content = decode_dict(cfg_file_content)
    params_file_content = file_io.read_file(config.files.params)[func.__name__]
    cfg_file_content["params"] = params_file_content

    loaded_cfg = NodeConfig(**cfg_file_content)
    loaded_cfg.convert_fields_to_dotdict()
    return func(loaded_cfg)


AnyOrNodeConfig = typing.Union[typing.Any, NodeConfig]


@znflow.nodify
def nodify(
    *,
    params: dict = None,
    outs: UnionDictListOfStrPath = None,
    outs_no_cache: UnionDictListOfStrPath = None,
    outs_persist: UnionDictListOfStrPath = None,
    outs_persist_no_cache: UnionDictListOfStrPath = None,
    metrics: UnionDictListOfStrPath = None,
    metrics_no_cache: UnionDictListOfStrPath = None,
    deps: UnionDictListOfStrPath = None,
    plots: UnionDictListOfStrPath = None,
    plots_no_cache: UnionDictListOfStrPath = None,
):
    """Wrapper Function to convert a function into a DVC Stage.

    Special Parameters
    ------------------
    params: dict
        for the params.yaml file context
    **kwargs: str|Path|list
        All other parameters are related to dvc run commands and can be a str / Path
        or a list of them

    References
    ----------
    https://dvc.org/doc/command-reference/run#options
    """
    cfg_ = NodeConfig(
        outs=outs,
        params=params,
        deps=deps,
        outs_no_cache=outs_no_cache,
        outs_persist=outs_persist,
        outs_persist_no_cache=outs_persist_no_cache,
        metrics=metrics,
        metrics_no_cache=metrics_no_cache,
        plots=plots,
        plots_no_cache=plots_no_cache,
    )

    def func_collector(func):
        """Required for decorator to work."""

        def wrapper(
            *,
            silent: bool = False,
            no_commit: bool = False,
            external: bool = False,
            always_changed: bool = False,
            no_exec: bool = True,
            force: bool = True,
            no_run_cache: bool = False,
            dry_run: bool = False,
            run: bool = None,
            exec_func=False,
        ) -> AnyOrNodeConfig:
            """Wrap the function.

            Parameters
            ----------
            exec_func: bool
                Set to true to execute the function core
            silent: bool
                If called with no_exec=False this allows to hide the output from the
                subprocess call.
            no_commit:
                dvc parameter
            external:
                dvc parameter
            always_changed:
                dvc parameter
            no_exec:
                dvc parameter
            run: bool,
                inverse of no_exec. Will overwrite no_exec if set.
            force:
                dvc parameter
            no_run_cache:
                dvc parameter
            dry_run: bool, default = False
                Only return the script but don't actually run anything

            Returns
            -------
            This function only returns the parsed_func when exec_func is True, otherwise
            it returns the NodeConfig

            """
            if run is not None:
                no_exec = not run
            if silent:
                log.warning(
                    "DeprecationWarning: silent was replaced by 'zntrack.config.log_level"
                    " = logging.ERROR'"
                )

            # Jupyter Notebook
            if config.nb_name is not None:
                module = f"{config.nb_class_path}.{func.__name__}"
                jupyter_class_to_file(nb_name=config.nb_name, module_name=func.__name__)
            else:
                module = module_handler(func)

            if exec_func:
                return execute_function_call(func)

            cfg = copy.deepcopy(cfg_)
            save_node_config_to_files(cfg=cfg, node_name=func.__name__)
            dvc_run_option = DVCRunOptions(
                no_commit=no_commit,
                external=external,
                always_changed=always_changed,
                no_run_cache=no_run_cache,
                force=force,
            )

            script = prepare_dvc_script(
                node_name=func.__name__,
                dvc_run_option=dvc_run_option,
                custom_args=cfg.write_dvc_command(func.__name__),
                nb_name=config.nb_name,
                module=module,
                func_or_cls=func.__name__,
            )

            if dry_run:
                return script
            run_dvc_cmd(script)

            if not no_exec:
                run_dvc_cmd(["repro", func.__name__])

            cfg.convert_fields_to_dotdict()
            return cfg

        wrapper.is_node = True

        return wrapper

    return func_collector
