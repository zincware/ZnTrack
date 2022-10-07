import pathlib

from zntrack import utils
from zntrack.core.zntrackoption import ZnTrackOption


class Meta(ZnTrackOption):
    zn_type = utils.ZnTypes.META
    file = utils.Files.dvc
    dvc_option = utils.DVCOptions.PARAMS

    def get_filename(self, instance) -> pathlib.Path:
        return

    def mkdir(self, instance):
        return

    def get_data_from_files(self, instance):
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
        if instance.__dict__.get(self.name) is utils.LazyOption:
            # do not save anything if __get__/__set__ was never used
            return
        utils.file_io.update_meta(
            file=utils.Files.dvc,
            node_name=instance.node_name,
            data={self.name: getattr(instance, self.name)},
        )
