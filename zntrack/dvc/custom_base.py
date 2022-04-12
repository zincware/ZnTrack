"""Custom base classes for e.g. plots to account for plots modify"""
import typing

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

    def modify(self, instance) -> typing.List[str]:
        """Get a dvc cmd to run plots modify"""
        script = [
            "dvc",
            "plots",
            "modify",
            self.get_filename(instance).as_posix(),
        ]
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
