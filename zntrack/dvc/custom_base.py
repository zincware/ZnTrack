"""Custom base classes for e.g. plots to account for plots modify"""
import copy
import logging
import pathlib
import typing

from zntrack import utils
from zntrack.core.zntrackoption import ZnTrackOption

log = logging.getLogger(__name__)


def update_iterable_paths(
    value, path
) -> typing.Union[typing.List[pathlib.Path], pathlib.Path]:
    """Update the value paths to be inside the given path

    Parameters
    ----------
    value: list|str|Path
    path: pathlib.Path
        New directory to save data to

    Returns
    -------
    new_data: list[pathlib.Path] | pathlib.Path
    """
    if value is None:
        return
    assert isinstance(path, pathlib.Path)
    log.warning(f"Updating paths '{value}' to point to '{path}'.")
    path.mkdir(exist_ok=True, parents=True)
    if isinstance(value, (list, tuple)):
        return [path / x for x in value]
    return path / value


class DVCOption(ZnTrackOption):
    def __init__(self, default_value=None, *, use_node_dir=False, **kwargs):
        """

        Parameters
        ----------
        default_value
        use_node_dir: bool (default=False)
            Update all paths set for this DVCOption to point to nodes/<node_name>/filename
            This allows to save files more easily outside the root directory and sort them
            into the nodes directories without using self.node_name / file_name somewhere
            in the init.
        kwargs
        """
        super().__init__(default_value=default_value, **kwargs)
        self.use_node_dir = use_node_dir

    def __set__(self, instance, value):
        """Save value to instance.__dict__"""
        if self.use_node_dir:
            if instance.__dict__.get(self.name) is not None:
                raise ValueError(
                    f"Can not set new value for {self.name} when using"
                    " `use_node_dir=True`"
                )

            log.error(instance.node_name)

            value = update_iterable_paths(
                value, pathlib.Path("nodes", instance.node_name)
            )

        self._instance = instance
        instance.__dict__[self.name] = value

    def __get__(self, instance, owner=None):
        self._instance = instance

        if instance is None:
            return self
        elif (
            (not instance.is_loaded)
            and (self.name not in instance.__dict__)
            and self.use_node_dir
        ):
            instance.__dict__[self.name] = update_iterable_paths(
                copy.deepcopy(self.default_value),
                pathlib.Path("nodes", instance.node_name),
            )
        else:
            self._write_instance_dict(instance)

        return instance.__dict__[self.name]


class PlotsModifyOption(DVCOption):
    def __init__(
        self,
        default_value=None,
        *,
        template=None,
        x=None,
        y=None,
        x_label=None,
        y_label=None,
        title=None,
        no_header=False,
        **kwargs,
    ):
        """
        See https://dvc.org/doc/command-reference/plots/modify for parameter information.
        """
        super().__init__(default_value=default_value, **kwargs)
        self.template = template
        self.x = x
        self.y = y
        self.x_label = x_label
        self.y_label = y_label
        self.title = title
        self.no_header = no_header

    def post_dvc_cmd(self, instance) -> typing.List[str]:
        """Get a dvc cmd to run plots modify"""
        if not any(
            [
                self.template,
                self.x,
                self.y,
                self.x_label,
                self.y_label,
                self.title,
                self.no_header,
            ]
        ):
            # don't run plots modify if no parameters are given.
            return None
        if self.zn_type in utils.FILE_DVC_TRACKED:
            # TODO this only works for a single file and not for a list of files
            filename = getattr(instance, self.name)
            if isinstance(filename, (list, tuple)):
                raise ValueError("Plots modify is currently not supported for lists")
            filename = pathlib.Path(filename).as_posix()  # only supports str
        else:
            filename = self.get_filename(instance).as_posix()

        script = ["dvc", "plots", "modify", filename]
        for key, value in [
            ("--template", self.template),
            ("-x", self.x),
            ("-y", self.y),
            ("--x-label", self.x_label),
            ("--y-label", self.y_label),
            ("--title", self.title),
        ]:
            if value is not None:
                script += [key, value]
        if self.no_header:
            script.append("--no-header")
        return script
