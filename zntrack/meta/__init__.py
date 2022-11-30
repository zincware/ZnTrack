"""ZnTrack Node meta data __init__.

Collection of Nodes that allow the storage of data inside a Node that is neither a true
parameter but also not an output. This can be e.g. information about the user, some
description but also e.g. different paths to binaries that should be used.
In principle, it is advisable to add the binary as a direct dependency but often
this is not feasible and can be circumvented by using 'meta'.
"""
import pathlib

from zntrack import utils
from zntrack.core.zntrackoption import ZnTrackOption


class Text(ZnTrackOption):
    """ZnTrack Text based meta descriptor.

    This ZnTrackOption allows the storage of plain text data in the 'dvc.yaml' meta key.
    """

    zn_type = utils.ZnTypes.META
    file = utils.Files.dvc
    dvc_option = utils.DVCOptions.PARAMS

    def get_filename(self, instance) -> pathlib.Path:
        """No File available."""
        return

    def mkdir(self, instance):
        """No directory to be created."""
        return

    def get_data_from_files(self, instance):
        """Load data from files."""
        try:
            file_content = utils.file_io.read_file(self.file)
        except FileNotFoundError as err:
            raise self._get_loading_errors(instance) from err

        try:
            values = file_content["stages"][instance.node_name]["meta"][self.name]
        except KeyError as err:
            raise self._get_loading_errors(instance) from err
        return values

    def save(self, instance):
        """Save data to file."""
        if instance.__dict__.get(self.name) is utils.LazyOption:
            # do not save anything if __get__/__set__ was never used
            return
        utils.file_io.update_meta(
            file=utils.Files.dvc,
            node_name=instance.node_name,
            data={self.name: getattr(instance, self.name)},
        )
