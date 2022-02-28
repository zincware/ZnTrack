from __future__ import annotations

import dataclasses
import logging
import pathlib
import typing

from zntrack import descriptor, utils
from zntrack.core.jupyter import jupyter_class_to_file
from zntrack.core.zntrackoption import ZnTrackOption

log = logging.getLogger(__name__)


def handle_deps(value) -> list:
    """Find all dependencies of value

    Parameters
    ----------
    value: any
        list, string, tuple, Path or Node instance

    Returns
    -------
    list:
        A list of strings like ["--deps", "<path>", --deps, "<path>", ...]

    """
    script = []
    if isinstance(value, (list, tuple)):
        for lst_val in value:
            script += handle_deps(lst_val)
    else:
        if isinstance(value, GraphWriter):
            for file in value.affected_files:
                script += ["--deps", pathlib.Path(file).as_posix()]
        elif isinstance(value, (str, pathlib.Path)):
            script += ["--deps", pathlib.Path(value).as_posix()]
        elif value is None:
            pass
        else:
            raise ValueError(f"Type {type(value)} ({value}) is not supported!")

    return script


@dataclasses.dataclass
class DVCRunOptions:
    """Collection of DVC run options

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
    no_exec: bool
    force: bool

    @property
    def dvc_args(self) -> list:
        """Get the activated options
        Returns
        -------
        list: A list of strings for the subprocess call, e.g.:
            ["--no-commit", "--external"]
        """
        out = []
        for field_name in self.__dataclass_fields__:
            value = getattr(self, field_name)
            if value:
                out.append(f"--{field_name.replace('_', '-')}")
        return out


def handle_dvc(value, dvc_args) -> list:
    """Convert list of dvc_paths to a dvc input string

    >>> handle_dvc("src/file.txt", "outs") == ["--outs", "src/file.txt"]
    """
    if not isinstance(value, (list, tuple)):
        value = [value]

    def option_func(_dvc_path):
        return f"--{dvc_args}"

    def posix_func(dvc_path):
        return pathlib.Path(dvc_path).as_posix()

    # double list comprehension https://stackoverflow.com/a/11869360/10504481
    return [f(x) for x in value for f in (option_func, posix_func)]


def filter_ZnTrackOption(
    data,
    cls,
    zntrack_type: typing.Union[str, list],
    return_with_type=False,
    allow_none: bool = False,
) -> dict:
    """Filter the descriptor instances by zntrack_type

    Parameters
    ----------
    data: List[ZnTrackOption]
        The ZnTrack options to query through
    cls:
        The instance the ZnTrack options are attached to
    zntrack_type: str
        The zntrack_type of the descriptors to gather
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
    if not isinstance(zntrack_type, list):
        zntrack_type = [zntrack_type]
    data = [x for x in data if x.zntrack_type in zntrack_type]
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
    if allow_none:
        return {x.name: getattr(cls, x.name, None) for x in data}
    # avoid AttributeError
    return {x.name: getattr(cls, x.name) for x in data}


def prepare_dvc_script(
    node_name, dvc_run_option, custom_args: list, nb_name, module, func_or_cls, call_args
) -> list:
    script = ["dvc", "run", "-n", node_name]
    script += dvc_run_option.dvc_args
    script += custom_args

    if nb_name is not None:
        script += ["--deps", utils.module_to_path(module).as_posix()]

    import_str = f"""{utils.get_python_interpreter()} -c "from {module} import """
    import_str += f"""{func_or_cls}; {func_or_cls}{call_args}" """
    script += [import_str]
    log.debug(f"dvc script: {' '.join([str(x) for x in script])}")
    return script


class GraphWriter:
    """Write the DVC Graph

    Main method that handles writing the Graph / dvc.yaml file
    """

    _node_name = None
    _module = None

    def __init__(self, **kwargs):
        self.node_name = kwargs.get("name", None)

    @property
    def _descriptor_list(self) -> typing.List[ZnTrackOption]:
        """Get all descriptors of this instance"""
        return descriptor.get_descriptors(self, ZnTrackOption)

    @property
    def node_name(self) -> str:
        """Name of this node"""
        if self._node_name is None:
            return self.__class__.__name__
        return self._node_name

    @node_name.setter
    def node_name(self, value):
        """Overwrite the default node name based on the class name"""
        self._node_name = value

    @property
    def module(self) -> str:
        """Module from which to import <name>

        Used for from <module> import <name>

        Notes
        -----
        this can be changed when using nb_mode
        """
        if self._module is None:
            return utils.module_handler(self.__class__)
        return self._module

    def save(self, results: bool = False):
        """Save Class state to files

        Parameters
        -----------
        results: bool, default=False
            Save changes in zn.<option>.
            By default, this function saves e.g. parameters but does not save results
            that are stored in zn.<option> and primarily zn.params / dvc.<option>
            Set this option to True if they should be saved, e.g. in run_and_save
        """
        raise NotImplementedError

    @property
    def affected_files(self) -> typing.Set[pathlib.Path]:
        """list of all files that can be changed by this instance"""
        files = []
        for option in self._descriptor_list:
            file = option.get_filename(self)
            if option.tracked:
                files.append(file)
            elif option.value_tracked:
                value = getattr(self, option.name)
                if isinstance(value, list):
                    files += value
                else:
                    files.append(value)

        files = [x for x in files if x is not None]
        return set(files)

    @classmethod
    def convert_notebook(cls, nb_name: str = None):
        """Use jupyter_class_to_file to convert ipynb to py

        Parameters
        ----------
        nb_name: str
            Notebook name when not using config.nb_name (this is not recommended)
        """
        jupyter_class_to_file(nb_name=nb_name, module_name=cls.__name__)

    def write_graph(
        self,
        silent: bool = False,
        nb_name: str = None,
        notebook: bool = True,
        no_commit: bool = False,
        external: bool = False,
        always_changed: bool = False,
        no_exec: bool = True,
        force: bool = True,
        no_run_cache: bool = False,
        dry_run: bool = False,
        run: bool = None,
    ):
        """Write the DVC file using run.

        If it already exists it'll tell you that the stage is already persistent and
        has been run before. Otherwise it'll run the stage for you.

        Parameters
        ----------
        silent: bool
            If called with no_exec=False this allows to hide the output from the
            subprocess call.
        nb_name: str
            Notebook name when not using config.nb_name (this is not recommended)
        notebook: bool, default = True
            convert the notebook to a py File
        no_commit: dvc parameter
        external: dvc parameter
        always_changed: dvc parameter
        no_exec: dvc parameter
        run: bool, inverse of no_exec. Will overwrite no_exec if set.
        force: dvc parameter
        no_run_cache: dvc parameter
        dry_run: bool, default = False
            Only return the script but don't actually run anything

        Notes
        -----
        If the dependencies for a stage change this function won't necessarily tell you.
        Use 'dvc status' to check, if the stage needs to be rerun.

        """

        if silent:
            log.warning(
                "DeprecationWarning: silent was replaced by 'zntrack.config.log_level ="
                " logging.ERROR'"
            )
        if run is not None:
            no_exec = not run

        log.debug("--- Writing new DVC file ---")

        dvc_run_option = DVCRunOptions(
            no_commit=no_commit,
            external=external,
            always_changed=always_changed,
            no_run_cache=no_run_cache,
            no_exec=no_exec,
            force=force,
        )

        # Jupyter Notebook
        nb_name = utils.update_nb_name(nb_name)
        if nb_name is not None:
            self._module = f"{utils.config.nb_class_path}.{self.__class__.__name__}"
            if notebook:
                self.convert_notebook(nb_name)

        custom_args = []
        # Handle Parameter
        params_list = filter_ZnTrackOption(
            data=self._descriptor_list,
            cls=self,
            zntrack_type=[utils.ZnTypes.params],
        )
        if len(params_list) > 0:
            custom_args += [
                "--params",
                f"{utils.Files.params}:{self.node_name}",
            ]
        zn_options_set = set()
        for option in self._descriptor_list:
            if option.zntrack_type == utils.ZnTypes.dvc:
                value = getattr(self, option.name)
                custom_args += handle_dvc(value, option.dvc_args)
            # Handle Zn Options
            elif option.zntrack_type in [
                utils.ZnTypes.results,
                utils.ZnTypes.metadata,
            ]:
                zn_options_set.add(
                    (
                        f"--{option.dvc_args}",
                        option.get_filename(self).as_posix(),
                    )
                )
            elif option.zntrack_type == utils.ZnTypes.deps:
                value = getattr(self, option.name)
                custom_args += handle_deps(value)

        for pair in zn_options_set:
            custom_args += pair

        script = prepare_dvc_script(
            node_name=self.node_name,
            dvc_run_option=dvc_run_option,
            custom_args=custom_args,
            nb_name=nb_name,
            module=self.module,
            func_or_cls=self.__class__.__name__,
            call_args=f".load(name='{self.node_name}').run_and_save()",
        )

        # Add command to run the script

        self.save()

        log.debug(
            "If you are using a jupyter notebook, you may not be able to see the "
            "output in real time!"
        )

        if dry_run:
            return script
        utils.run_dvc_cmd(script)
