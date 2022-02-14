import logging
import pathlib

import pandas as pd

from zntrack import utils
from zntrack.core.parameter import File, ZnTrackOption
from zntrack.descriptor import Metadata
from zntrack.utils.lazy_loader import LazyOption

log = logging.getLogger(__name__)


class plots(ZnTrackOption):
    metadata = Metadata(dvc_option="plots_no_cache", zntrack_type=utils.ZnTypes.results)

    def get_filename(self, instance) -> File:
        """Overwrite filename to csv"""
        return File(
            path=pathlib.Path(
                "nodes", instance.node_name, f"{self.metadata.dvc_option}.csv"
            ),
            tracked=True,
        )

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
        file.path.parent.mkdir(exist_ok=True, parents=True)
        value.to_csv(file.path)

    def update_instance(self, instance, lazy):
        """Load value with pd.read_csv"""
        if lazy:
            instance.__dict__.update({self.name: LazyOption})
        else:
            file = self.get_filename(instance)
            try:
                instance.__dict__.update({self.name: pd.read_csv(file.path, index_col=0)})
            except (FileNotFoundError, KeyError):
                pass
