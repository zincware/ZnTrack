"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: zn.<option>

The following can be used to store e.g. metrics directly without
defining and writing to a file
"""
import json
import logging
import pathlib

import znjson

from zntrack.core.parameter import File, ZnTrackOption
from zntrack.descriptor import Metadata
from zntrack.utils import file_io

log = logging.getLogger(__name__)


# module class definitions to be used via zn.<option>
# detailed explanations on https://dvc.org/doc/command-reference/run#options
# with the exception that these will be loaded to memory when.
# for direct file references use dvc.<option> instead.


class outs(ZnTrackOption):
    metadata = Metadata(dvc_option="outs", zntrack_type="zn")


class deps(ZnTrackOption):
    metadata = Metadata(dvc_option="deps", zntrack_type="deps")


class metrics(ZnTrackOption):
    metadata = Metadata(dvc_option="metrics_no_cache", zntrack_type="zn")


class params(ZnTrackOption):
    metadata = Metadata(dvc_option="params", zntrack_type="params")


class iterable(ZnTrackOption):
    metadata = Metadata(dvc_option="params", zntrack_type="iterable")


class metadata(ZnTrackOption):
    metadata = Metadata(dvc_option="metrics_no_cache", zntrack_type="metadata")


class Method(ZnTrackOption):
    """ZnTrack methods passing descriptor

    This descriptor allows to pass a class instance that is not a ZnTrack Node as a
    method that can be used later. It requires that all passed class attributes have
    the same name in the __init__ and via getattr an that they are serializable.

    Example
    --------
    >>> class HelloWorld:
    >>>     def __init__(self, name):
    >>>         self.name = name
    >>>
    >>> class MyNode(zntrack.Node)
    >>>     my_method = Method()
    >>> MyNode().my_method = HelloWorld(name="Max")

    """

    metadata = Metadata(dvc_option="params", zntrack_type="method")

    def get_filename(self, instance) -> File:
        """Does not really have a single file but params.yaml and zntrack.json"""
        return File(path=pathlib.Path("params.yaml"))

    def save(self, instance):
        """Overwrite the save method

        For methods saving is split between params.yaml for the parameters and
        zntrack.json for the class to be imported and instantiated.
        """
        value = self.__get__(instance, self.owner)
        serialized_value = json.loads(json.dumps(value, cls=znjson.ZnEncoder))

        # Write to params.yaml
        file_io.update_config_file(
            file=pathlib.Path("params.yaml"),
            node_name=instance.node_name,
            value_name=self.name,
            value=serialized_value["value"].pop("kwargs"),
        )

        # write to zntrack.json
        file_io.update_config_file(
            file=pathlib.Path("zntrack.json"),
            node_name=instance.node_name,
            value_name=self.name,
            value=serialized_value,
        )

    def load(
        self, instance, raise_file_error: bool = False, raise_key_error: bool = True
    ):
        """Overwrite the load method

        For methods loading is split between params.yaml for the parameters and
        zntrack.json for the class to be imported and instantiated.
        """
        file = self.get_filename(instance)
        try:
            params = file_io.read_file(pathlib.Path("params.yaml"))[instance.node_name][
                self.name
            ]
            cls_dict = file_io.read_file(pathlib.Path("zntrack.json"))[
                instance.node_name
            ][self.name]

            cls_dict["value"]["kwargs"] = params
            value = json.loads(json.dumps(cls_dict), cls=znjson.ZnDecoder)

            log.debug(f"Loading {file.key} from {file}: ({value})")
            instance.__dict__.update({self.name: value})
        except FileNotFoundError as e:
            if raise_file_error:
                raise e
            else:
                pass
        except KeyError as e:
            if raise_key_error:
                raise e
            else:
                pass

    def __get__(self, instance, owner):
        """Add some custom attributes to the instance to identify it in znjson"""
        if instance is None:
            return self
        log.debug(f"Get {self} from {instance}")
        value = instance.__dict__.get(self.name, self.default_value)
        # Set some attribute for the serializer
        value.znjson_zn_method = True
        value.znjson_module = instance.module
        return value
