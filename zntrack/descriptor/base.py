from __future__ import annotations

import dataclasses
import json
import logging
import pathlib
import typing

import yaml
import znjson

log = logging.getLogger(__name__)


@dataclasses.dataclass
class Metadata:
    dvc_option: str
    zntrack_type: str

    @property
    def dvc_args(self):
        return self.dvc_option.replace("_", "-")


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
            if value is None:
                continue
            if option.metadata.zntrack_type == "zn":
                # Handle Zn Options
                files.append(
                    pathlib.Path("nodes")
                    / self.node_name
                    / f"{option.metadata.dvc_option}.json"
                )
            elif option.metadata.zntrack_type == "dvc":
                if isinstance(value, list) or isinstance(value, tuple):
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
    def _save_file(file: pathlib.Path, value: dict):
        """Save dict to file

        Store dictionary to json or yaml file

        Parameters
        ----------
        file: pathlib.Path
            File to save to
        value: dict
            Any serializable data to save
        """
        if file.suffix == ".yaml":
            with file.open("w") as f:
                yaml.safe_dump(value, f, indent=4)
        elif file.suffix == ".json":
            file.write_text(json.dumps(value, indent=4))

    def _save_to_file(self, file: pathlib.Path, zntrack_type: str, key: str = None):
        file = pathlib.Path(file)  # optional

        try:
            file_content = self._read_file(file)
        except FileNotFoundError:
            file_content = {}

        values = self._descriptor_list.filter(zntrack_type)
        if key:
            file_content[key] = values
        else:
            file_content = values

        log.debug(f"Saving {key} to {file}: ({values})")
        self._save_file(file, file_content)

    def _load_from_file(self, file: pathlib.Path, key: str = None):
        file = pathlib.Path(file)  # optional
        file_content = self._read_file(file)
        if key is not None:
            values = file_content[key]
        else:
            values = file_content
        log.debug(f"Loading {key} from {file}: ({values})")
        self.__dict__.update(values)

    @property
    def node_name(self):
        if self._node_name is None:
            return self.__class__.__name__
        return self._node_name

    @node_name.setter
    def node_name(self, value):
        self._node_name = value


class Descriptor:
    metadata: Metadata = None

    def __init__(self, default_value=None):
        self.default_value = default_value
        self.owner = None
        self.instance = None
        self.name = ""

    def __set_name__(self, owner, name):
        self.owner = owner
        self.name = name

    def get(self, instance, owner):
        """Overwrite this method for custom get method"""
        raise NotImplementedError

    def set(self, instance, value):
        """Overwrite this method for custom set method"""
        raise NotImplementedError

    def __get__(self, instance, owner):
        if instance is None:
            return self
        log.debug(f"Get {self} from {instance}")
        try:
            return self.get(instance, owner)
        except NotImplementedError:
            return instance.__dict__.get(self.name, self.default_value)

    def __set__(self, instance, value):
        log.debug(f"Set {self} from {instance}")
        try:
            self.set(instance, value)
        except NotImplementedError:
            instance.__dict__[self.name] = value
