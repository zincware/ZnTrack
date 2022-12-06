"""Custom base classes for e.g. plots to account for plots modify."""
import logging
import pathlib
import typing

import zninit

from zntrack import utils
from zntrack.core.zntrackoption import ZnTrackOption
from zntrack.utils.nwd import replace_nwd_placeholder

log = logging.getLogger(__name__)


class DVCOption(ZnTrackOption):
    """Allow for nwd placeholder in strings to be automatically replaced."""

    def __get__(self, instance, owner=None, serialize=False):
        """Overwrite getter to replace nwd placeholder when read the first time."""
        # TODO maybe make this a mixin?
        self._instance = instance

        if instance is None:
            return self
        else:
            self._write_instance_dict(instance)

        # this is a cheap operation, so we run this every single time.
        if serialize:
            return instance.__dict__[self.name]
        return replace_nwd_placeholder(
            instance.__dict__[self.name], node_working_directory=instance.nwd
        )


class PlotsModifyOption(DVCOption):
    """Descriptor to allow plots to be modified."""

    def __init__(
        self,
        default=zninit.descriptor.Empty,
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
        """PlotsModifyOption.

        See https://dvc.org/doc/command-reference/plots/modify for parameter information.
        """
        super().__init__(default=default, **kwargs)
        self.template = template
        self.x = x
        self.y = y
        self.x_label = x_label
        self.y_label = y_label
        self.title = title
        self.no_header = no_header

    def post_dvc_cmd(self, instance) -> typing.List[str]:
        """Get a dvc cmd to run plots modify."""
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

        script = ["plots", "modify", filename]
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
