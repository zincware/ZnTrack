import yaml
import znflow
import znjson

from . import config, converter


class Project(znflow.DiGraph):
    def build(self) -> None:
        config.PARAMS_FILE_PATH.write_text(
            yaml.safe_dump(converter.convert_graph_to_parameter(self))
        )
        config.DVC_FILE_PATH.write_text(
            yaml.safe_dump(converter.convert_graph_to_dvc_config(self))
        )
        config.ZNTRACK_FILE_PATH.write_text(
            znjson.dumps(
                converter.convert_graph_to_zntrack_config(self),
                indent=2,
                cls=znjson.ZnEncoder.from_converters(
                    [converter.ConnectionConverter, converter.NodeConverter],
                    add_default=True,
                ),
            )
        )
