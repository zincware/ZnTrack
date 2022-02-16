import logging
import pathlib

import pandas as pd

from zntrack import utils
from zntrack.core.parameter import ZnTrackOption

log = logging.getLogger(__name__)


class plots(ZnTrackOption):
    dvc_option = "plots_no_cache"
    zntrack_type = utils.ZnTypes.results
    tracked = True

    def get_filename(self, instance) -> pathlib.Path:
        """Overwrite filename to csv"""
        return pathlib.Path("nodes", instance.node_name, f"{self.dvc_option}.csv")

    def save(self, instance):
        """Save value with pd.DataFrame.to_csv"""
        value = self.__get__(instance, self.owner)

        if value is None:
            return

        if not isinstance(value, pd.DataFrame):
            raise TypeError(
                f"zn.plots() only supports <pd.DataFrame> and not {type(value)}"
            )

        if value.index.name is None:
            raise ValueError(
                "pd.DataFrame must have an index name! You can set the name via"
                " DataFrame.index.name = <index name>."
            )

        file = self.get_filename(instance)
        file.parent.mkdir(exist_ok=True, parents=True)
        value.to_csv(file)

    def update_instance(self, instance):
        """Load value with pd.read_csv"""

        file = self.get_filename(instance)
        try:
            instance.__dict__.update({self.name: pd.read_csv(file, index_col=0)})
        except (FileNotFoundError, KeyError):
            pass
