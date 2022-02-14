"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: zn.<option>

The following can be used to store e.g. metrics directly without
defining and writing to a file explicitly. For more information on the individual methods
see https://dvc.org/doc/command-reference/run#options

"""
import json
import logging

import znjson

from zntrack import utils
from zntrack.core.parameter import File, ZnTrackOption
from zntrack.descriptor import Metadata

log = logging.getLogger(__name__)

try:
    from .plots import plots

    __all__ = [plots.__name__]
except ImportError:
    pass


# module class definitions to be used via zn.<option>
# detailed explanations on https://dvc.org/doc/command-reference/run#options
# with the exception that these will be loaded to memory when.
# for direct file references use dvc.<option> instead.


def split_value(input_val):
    """Split input_val into data for params.yaml and zntrack.json"""
    try:
        # zn.Method
        params_data = input_val["value"].pop("kwargs")
    except (AttributeError, TypeError):
        # everything else
        params_data = input_val.pop("value")
    return params_data, input_val


def combine_values(cls_dict: dict, params_val):
    """Combine values from params.yaml and zntrack.json

    Parameters
    ----------
    cls_dict: dict
        loaded from zntrack.json
    params_val:
        Parameters from params.yaml

    Returns
    -------
    Loaded object of type cls_dict[_type]

    """
    try:
        # zn.Method
        cls_dict["value"]["kwargs"] = params_val
    except KeyError:
        # everything else
        cls_dict["value"] = params_val

    return json.loads(json.dumps(cls_dict), cls=znjson.ZnDecoder)


class SplitZnTrackOption(ZnTrackOption):
    """Method to split a value into params.yaml and zntrack.json

    Serialize data into params.yaml if human-readable and the type in zntrack.json
    """

    def save(self, instance):
        """Overwrite the save method

        This save method tries to split the value into params.yaml and zntrack.json.
        This allows e.g. having pathlib.Path() as a zn.params or a dataclass as zn.Method
        where the path as string / the dataclass as dict is stored in params.yaml
        """
        value = self.__get__(instance, self.owner)
        serialized_value = json.loads(json.dumps(value, cls=znjson.ZnEncoder))

        try:
            # if znjson was used to serialize the data, it will have a _type key
            if isinstance(serialized_value, list):
                data = [split_value(x) for x in serialized_value]
                params_data, zntrack_data = zip(*data)
            else:
                # Check that correctly serialized
                _ = serialized_value["_type"]
                params_data, zntrack_data = split_value(serialized_value)

            # Write to params.yaml
            utils.file_io.update_config_file(
                file=utils.Files.params,
                node_name=instance.node_name,
                value_name=self.name,
                value=params_data,
            )

            # write to zntrack.json
            utils.file_io.update_config_file(
                file=utils.Files.zntrack,
                node_name=instance.node_name,
                value_name=self.name,
                value=zntrack_data,
            )
        except (KeyError, AttributeError, TypeError):
            # KeyError if serialized_value is a normal dict
            # AttributeError when serialized_value.pop does not exist
            # TypeError <..>
            super().save(instance)

    def load(self, instance):
        """Overwrite the load method

        Try to load from zntrack.json / params.yaml in a combined approach first,
        if no entry in zntrack.json is found, load from params.yaml only without
        deserializing.
        """
        file = self.get_filename(instance)

        try:
            # Check that we can read it
            _ = utils.file_io.read_file(utils.Files.zntrack)[instance.node_name][
                self.name
            ]

            params_values = utils.file_io.read_file(utils.Files.params)
            cls_dict = utils.file_io.read_file(utils.Files.zntrack)
            # select <node><attribute> from the full params / zntrack file
            params_values = params_values[instance.node_name][self.name]
            cls_dict = cls_dict[instance.node_name][self.name]

            if isinstance(cls_dict, list):
                value = [combine_values(*x) for x in zip(cls_dict, params_values)]
            else:
                value = combine_values(cls_dict, params_values)

            log.debug(f"Loading {file.key} from {file}: ({value})")
            instance.__dict__.update({self.name: value})
        except (AttributeError, KeyError, TypeError, FileNotFoundError):
            super().load(instance)


class outs(ZnTrackOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    metadata = Metadata(dvc_option="outs", zntrack_type=utils.ZnTypes.results)


class deps(ZnTrackOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    metadata = Metadata(dvc_option="deps", zntrack_type=utils.ZnTypes.deps)
    file = utils.Files.zntrack


class metrics(ZnTrackOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    metadata = Metadata(dvc_option="metrics_no_cache", zntrack_type=utils.ZnTypes.results)


class params(SplitZnTrackOption):
    """Identify DVC option

    See https://dvc.org/doc/command-reference/run#options for more information
     on the available options
    """

    metadata = Metadata(dvc_option="params", zntrack_type=utils.ZnTypes.params)
    file = utils.Files.params


class iterable(ZnTrackOption):
    """Speciel ZnTrack option

    This option defines an iterable parameter for spawning nodes.
    """

    metadata = Metadata(dvc_option="params", zntrack_type=utils.ZnTypes.iterable)


class metadata(ZnTrackOption):
    """Speciel ZnTrack option

    This option defines a <metrics_no_cache> output that is used by ZnTracks metadata
    collectors.
    """

    metadata = Metadata(
        dvc_option="metrics_no_cache", zntrack_type=utils.ZnTypes.metadata
    )


class Method(SplitZnTrackOption):
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

    metadata = Metadata(dvc_option="params", zntrack_type=utils.ZnTypes.params)

    def get_filename(self, instance) -> File:
        """Does not really have a single file but params.yaml and zntrack.json"""
        return File(path=utils.Files.params)

    def __get__(self, instance, owner):
        """Add some custom attributes to the instance to identify it in znjson"""
        if instance is None:
            return self
        log.debug(f"Get {self} from {instance}")
        value = instance.__dict__.get(self.name, self.default_value)
        if value is None:
            log.warning(
                "Found NoneType but expected some class instance. Please open an issue on"
                " github.com/zincware/ZnTrack if this causes unexpected behaviour."
            )
            return
        try:
            # Set some attribute for the serializer
            value.znjson_zn_method = True
            value.znjson_module = instance.module
        except AttributeError:
            # could be list / tuple
            for element in value:
                element.znjson_zn_method = True
                element.znjson_module = instance.module
        return value
