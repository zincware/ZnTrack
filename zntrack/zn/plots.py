"""ZnTrack plots descriptor."""
import logging
import pathlib

import pandas as pd

from zntrack import utils
from zntrack.dvc.custom_base import PlotsModifyOption

log = logging.getLogger(__name__)


class plots(PlotsModifyOption):  # pylint: disable=invalid-name
    """ZnTrack plots class."""

    dvc_option = utils.DVCOptions.PLOTS.value
    zn_type = utils.ZnTypes.PLOTS

    def __init__(self, *args, cache: bool = True, **kwargs):
        """Parse additional attributes for plots.

        Parameters
        ----------
        cache: bool, default = True
            Store the result of 'zn.plots' inside the DVC cache. If False
            store the results as 'dvc plots-no-cache'.
        args:
            positional arguments passed super.__init__
        kwargs:
            keyword arguments passed to super.__init__
        """
        if not cache:
            self.dvc_option = utils.DVCOptions.PLOTS_NO_CACHE.value
        super().__init__(*args, **kwargs)

    def get_filename(self, instance) -> pathlib.Path:
        """Overwrite filename to csv."""
        return instance.nwd / f"{self.name}.csv"

    def save(self, instance):
        """Save value with pd.DataFrame.to_csv."""
        value = self.__get__(instance, self.owner)

        if not isinstance(value, pd.DataFrame):
            raise TypeError(
                f"zn.plots() only supports <pd.DataFrame> and not {type(value)}"
            )

        if value.index.name is None:
            value.index.name = "index"

        file = self.get_filename(instance)
        file.parent.mkdir(exist_ok=True, parents=True)
        value.to_csv(file)

    def get_data_from_files(self, instance):
        """Load value with pd.read_csv."""
        file = self.get_filename(instance)
        return pd.read_csv(file, index_col=0)

    def __get__(self, instance, owner=None, serialize=False):
        """__get__ method."""
        self._instance = instance

        if instance is None:
            return self
        else:
            self._write_instance_dict(instance)
        return instance.__dict__[self.name]
