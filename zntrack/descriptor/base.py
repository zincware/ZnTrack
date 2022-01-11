from __future__ import annotations

import dataclasses
import json
import logging
import pathlib
import typing

import yaml
import znjson

from .descriptor import Descriptor

log = logging.getLogger(__name__)


@dataclasses.dataclass
class DescriptorList:
    parent: DescriptorIO
    data: typing.List[Descriptor] = dataclasses.field(default_factory=list)

    def filter(self, zntrack_type, return_with_type=False):
        data = [x for x in self.data if x.metadata.zntrack_type == zntrack_type]
        if return_with_type:
            types_dict = {x.metadata.dvc_option: {} for x in data}
            for x in data:
                types_dict[x.metadata.dvc_option].update(
                    {x.name: getattr(self.parent, x.name)}
                )
            return types_dict
        return {x.name: getattr(self.parent, x.name) for x in data}


class DescriptorIO:
    params_file = pathlib.Path("params.yaml")
    zntrack_file = pathlib.Path("zntrack.json")

    _node_name = None

    def __init__(self, name=None):
        self.node_name = name

    @property
    def _descriptor_list(self) -> DescriptorList:
        """Get all descriptors of this instance"""
        descriptor_list = []
        for option in vars(type(self)).values():
            if isinstance(option, Descriptor):
                descriptor_list.append(option)
        return DescriptorList(parent=self, data=descriptor_list)

    @property
    def affected_files(self) -> typing.Set[pathlib.Path]:
        """list of all files that can be changed by this instance"""
        files = []
        for option in self._descriptor_list.data:
            value = getattr(self, option.name)
            if option.metadata.zntrack_type == "zn":
                # Handle Zn Options
                files.append(
                    pathlib.Path("nodes")
                    / self.node_name
                    / f"{option.metadata.dvc_option}.json"
                )
            elif option.metadata.zntrack_type == "dvc":
                if value is None:
                    pass
                elif isinstance(value, list) or isinstance(value, tuple):
                    files += [pathlib.Path(x) for x in value]
                else:
                    files.append(pathlib.Path(value))
        return set(files)

    @staticmethod
    def _read_file(file: pathlib.Path) -> dict:
        """Read a json/yaml file

        Parameters
        ----------
        file: pathlib.Path
            The file to read

        Returns
        -------
        dict:
            Content of the json/yaml file
        """
        if file.suffix in [".yaml", ".yml"]:
            with file.open("r") as f:
                file_content = yaml.safe_load(f)
        elif file.suffix == ".json":
            file_content = json.loads(file.read_text())
        else:
            raise NotImplementedError(f"File with suffix {file.suffix} is not supported")
        return file_content

    @staticmethod
    def _write_file(file: pathlib.Path, value: dict):
        """Save dict to file

        Store dictionary to json or yaml file

        Parameters
        ----------
        file: pathlib.Path
            File to save to
        value: dict
            Any serializable data to save
        """
        if file.suffix in [".yaml", ".yml"]:
            with file.open("w") as f:
                yaml.safe_dump(value, f, indent=4)
        elif file.suffix == ".json":
            file.write_text(json.dumps(value, indent=4, cls=znjson.ZnEncoder))

    def _save_to_file(self, file: pathlib.Path, zntrack_type: str, key: str = None):
        file = pathlib.Path(file)  # optional

        try:
            file_content = self._read_file(file)
        except FileNotFoundError:
            file_content = {}

        values = self._descriptor_list.filter(zntrack_type)
        if key is not None:
            file_content[key] = values
        else:
            file_content = values

        log.debug(f"Saving {key} to {file}: ({values})")
        self._write_file(file, file_content)

    def _load_from_file(
        self, file: pathlib.Path, key: str = None, raise_error: bool = False
    ):
        try:
            file = pathlib.Path(file)  # optional
            file_content = self._read_file(file)
            # The problem here is, that I can not / don't want to load all Nodes but only
            # the ones, that are in [self.node_name], so we only deserialize them
            if key is not None:
                values = json.loads(json.dumps(file_content[key]), cls=znjson.ZnDecoder)
            else:
                values = json.loads(json.dumps(file_content), cls=znjson.ZnDecoder)
            log.debug(f"Loading {key} from {file}: ({values})")
            self.__dict__.update(values)
        except FileNotFoundError as e:
            if raise_error:
                raise e
            else:
                pass

    @property
    def node_name(self):
        if self._node_name is None:
            return self.__class__.__name__
        return self._node_name

    @node_name.setter
    def node_name(self, value):
        self._node_name = value
