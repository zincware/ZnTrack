"""Custom base classes for e.g. plots to account for plots modify"""
import pathlib
import typing

from zntrack import utils
from zntrack.core.zntrackoption import ZnTrackOption


class PlotsModifyOption(ZnTrackOption):
    def __init__(
        self,
        default_value=None,
        *,
        x=None,
        y=None,
        x_label=None,
        y_label=None,
        title=None,
        no_header=False,
        **kwargs
    ):
        """
        See https://dvc.org/doc/command-reference/plots/modify for parameter information.
        """
        super().__init__(default_value=default_value, **kwargs)
        self.x = x
        self.y = y
        self.x_label = x_label
        self.y_label = y_label
        self.title = title
        self.no_header = no_header

    def post_dvc_cmd(self, instance) -> typing.List[str]:
        """Get a dvc cmd to run plots modify"""
        if not any(
            [self.x, self.y, self.x_label, self.y_label, self.title, self.no_header]
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
