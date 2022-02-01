import dataclasses
import json
import pathlib
import subprocess
import typing

import dot4dict
import yaml
import znjson

from zntrack.utils.utils import module_handler

str_or_path = typing.Union[str, pathlib.Path]


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

    def write_dvc_command(self, node_name, import_str):
        script = ["dvc", "run", "-n", node_name]
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

        def wrapper(*, run=False, no_exec=False):
            """Wrap the function

            Parameters
            ----------
            run: bool
                Set to true to execute the function core
            no_exec: bool
                Only print the script that would be called

            Returns
            -------
            This function always returns None

            """
            cfg_file = pathlib.Path("zntrack.json")
            if run:
                # TODO load from zntrack.json and params.yaml
                cfg_json = json.loads(cfg_file.read_text(), cls=znjson.ZnDecoder)
                cfg = NodeConfig(**cfg_json)
                cfg.params = dot4dict.dotdict(cfg.params)
                return func(cfg)
            else:
                cfg = NodeConfig(outs, deps, params)
                cfg_file.write_text(
                    json.dumps(dataclasses.asdict(cfg), cls=znjson.ZnEncoder)
                )
                params_file = pathlib.Path("params.yaml")
                params_dict = {func.__name__: dataclasses.asdict(cfg)["params"]}
                params_file.write_text(yaml.safe_dump(params_dict))

            module = module_handler(func)

            import_str = f"""
            python -c "from {module} import {func.__name__};{func.__name__}(run=True)"
            """
            script = cfg.write_dvc_command(func.__name__, import_str)

            if no_exec:
                print(script)
            else:
                subprocess.check_call(script)
            return None

        return wrapper

    return func_collector
