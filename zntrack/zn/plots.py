import logging
import pathlib

import pandas as pd

from zntrack import utils
from zntrack.core.zntrackoption import ZnTrackOption

log = logging.getLogger(__name__)


class plots(ZnTrackOption):
    dvc_option = utils.DVCOptions.PLOTS_NO_CACHE.value
    zn_type = utils.ZnTypes.RESULTS

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

    def get_data_from_files(self, instance):
        """Load value with pd.read_csv"""

        file = self.get_filename(instance)
        return pd.read_csv(file, index_col=0)
