import dataclasses
import logging
import pathlib
import subprocess
import typing

import dot4dict

from zntrack.utils import file_io, utils

str_or_path = typing.Union[str, pathlib.Path]

log = logging.getLogger(__name__)


@dataclasses.dataclass
class NodeConfig:
    """DataClass to contain the arguments passed by the user

    Attributes
    ----------
    All dvc attributes but connected by "_" instead of "-"

    """

    outs: typing.Union[str_or_path, typing.List[str_or_path]] = None
    deps: typing.Union[str_or_path, typing.List[str_or_path]] = None
    params: dot4dict.dotdict = dataclasses.field(default_factory=dict)

    def write_dvc_command(self, node_name, import_str, no_exec: bool):
        script = ["dvc", "run", "-n", node_name, "--force"]
        if no_exec:
            script += ["--no-exec"]
        if self.params is not None:
            if len(self.params) > 0:
                script += ["--params", f"params.yaml:{node_name}"]
        for field in self.__dataclass_fields__:
            if field == "params":
                continue
            if isinstance(getattr(self, field), (list, tuple)):
                for element in getattr(self, field):
                    script += [f"--{field.replace('_', '-')}", str(element)]
            elif getattr(self, field) is not None:
                script += [f"--{field.replace('_', '-')}", str(getattr(self, field))]

        script.append(import_str)

        return script


any_or_nodeconfig = typing.Union[typing.Any, NodeConfig]


def nodify(outs=None, deps=None, params=None):
    """Main wrapper Function

    Parameters
    ----------
    outs: str|Path|list
        for dvc run --outs
    deps: str|Path|list
        for dvc run --deps
    params: dict
        for the params.yaml file context
    """
    if not isinstance(params, dict) and params is not None:
        raise ValueError("Parameter must be dict or dot4dict.dotdict.")

    def func_collector(func):
        """Required for decorator to work"""

        def wrapper(*, run=None, no_exec=True, exec_func=False) -> any_or_nodeconfig:
            """Wrap the function

            Parameters
            ----------
            exec_func: bool
                Set to true to execute the function core
            run: bool, default=False
                opposite of no_exec with higher priority
            no_exec: bool, default=True
                dvc parameter

            Returns
            -------
            This function only returns the parsed_func when exec_func is True, otherwise
            it returns the NodeConfig

            """
            if run is not None:
                no_exec = not run

            cfg_file = pathlib.Path("zntrack.json")
            params_file = pathlib.Path("params.yaml")
            if exec_func:
                # TODO should exec_func always load from file or check if values
                #  are passed and then update the files?
                cfg_file_content = file_io.read_file(cfg_file)[func.__name__]
                cfg_file_content = utils.decode_dict(cfg_file_content)
                params_file_content = file_io.read_file(params_file)[func.__name__]
                cfg_file_content["params"] = params_file_content

                cfg = NodeConfig(**cfg_file_content)
                cfg.params = dot4dict.dotdict(cfg.params)
                return func(cfg)
            else:
                cfg = NodeConfig(outs, deps, params)
                for value_name, value in dataclasses.asdict(cfg).items():
                    if value_name == "params":
                        file_io.update_config_file(
                            file=params_file,
                            node_name=func.__name__,
                            value_name=None,
                            value=value,
                        )
                    else:
                        file_io.update_config_file(
                            file=cfg_file,
                            node_name=func.__name__,
                            value_name=value_name,
                            value=value,
                        )

            module = utils.module_handler(func)

            import_str = f"""python -c "from {module} import {func.__name__};"""
            import_str += f"""{func.__name__}(exec_func=True)" """
            script = cfg.write_dvc_command(func.__name__, import_str, no_exec=no_exec)
            log.debug(f"Running script: {script}")
            subprocess.check_call(script)

            return cfg

        return wrapper

    return func_collector
