"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: PyTrack parameter
"""
from __future__ import annotations
import logging
import typing

from pytrack.utils.types import NoneType

log = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from pytrack.utils.type_hints import TypeHintParent


class PyTrackOption:
    def __init__(self, option, default_value, name=None):
        self.option = option
        self.default_value = default_value
        self.name = name

        if option == "result" and default_value is not NoneType:
            raise ValueError(f"Can not pre-initialize result! Found {default_value}")

        self.check_input(default_value)

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance: TypeHintParent, owner):
        log.warning(f"Getting {self.option} / {self.name} for {instance}")
        try:
            return instance.__dict__[self.name]
        except KeyError:
            log.warning('KeyError: returning default value')
            if self.default_value is NoneType:
                return None
            return self.default_value
        except AttributeError:
            log.warning(f'No value found for {self.option} / {self.name} '
                        f'- returning default')
            # This can happen, when instance has not been instantiated, yielding in no
            #  __dict__ attribute. Returning the default value here.
            return self.default_value

    def __set__(self, instance: TypeHintParent, value):
        log.warning(f"Changing {self.option} / {self.name} to {value}")

        if isinstance(value, PyTrackOption):
            log.warning(f'{self.option} / {self.name} is already a PyTrackOption - '
                        f'Skipping updating it!')
            return

        if instance.pytrack.load and self.option != "result":
            raise ValueError(f'Changing {self.option} is currently not allowed!')

        if not instance.pytrack.running and self.option == "result":
            raise ValueError(f'Changing {self.option} is currently not allowed')

        self.check_input(value)

        instance.__dict__[self.name] = value

    def check_input(self, value):
        """Check if the input value can be processed"""
        if isinstance(value, dict):
            log.warning(
                f"Used mutable type dict for {self.option}! "
                f"Always overwrite the {self.option} and don't alter it "
                f"otherwise!, It won't work."
            )

        if isinstance(value, list):
            log.warning(
                f"Used mutable type list for {self.option}! "
                f"Always overwrite the {self.option} and don't append "
                f"to it! It won't work."
            )


class LazyProperty:
    """Lazy property that takes the attribute name for PyTrackOption definition"""

    def __set_name__(self, owner, name):
        """Descriptor default"""
        self.name = name

    def __get__(self, instance, owner):
        def pass_name(value=NoneType) -> PyTrackOption:
            """
            Parameters
            ----------
            value: any
                Any value to be passed as default to the PyTrackOption

            Returns
            -------
            instantiated PyTrackOption with correct set name and default values

            """
            return PyTrackOption(option=self.name, default_value=value)

        return pass_name


class DVC:
    params = LazyProperty()
    result = LazyProperty()
    deps = LazyProperty()
    outs = LazyProperty()
    metrics_no_cache = LazyProperty()

# class _PyTrackOption:
#     def __init__(
#             self,
#             value=None,
#             option: str = None,
#             attr: str = None,
#             cls: TypeHintParent = None,
#     ):
#         """PyTrack Descriptor to handle the loading and writing of files
#
#         Parameters
#         ----------
#         option: str
#             One of the DVC options, e.g., params, outs, ...
#         value:
#             default value
#         attr
#         cls
#         """
#         if option is None:
#             log.warning("Using a custom PyTrackOption! No default values supported!")
#             option = "custom"
#
#         self.pytrack_dvc_option = option
#         self.value = value
#         self.check_input(value)
#
#         if value is not None and cls is not None:
#             value = self.get_value(value)
#             if value is NoneType:
#                 return
#
#             value = serializer(value)
#             self.set_internals(cls, {attr: value})
#
#     def __get__(self, instance: TypeHintParent, owner):
#         """Get the value of this instance from pytrack_internals and return it"""
#         try:
#             return self._get(instance, owner)
#         except NotImplementedError:
#             if self.pytrack_dvc_option == "result":
#                 return deserializer(
#                     self.get_results(instance).get(self.get_name(instance))
#                 )
#             else:
#                 output = self.get_internals(instance).get(self.get_name(instance), "")
#                 output = deserializer(output)
#                 if self.pytrack_dvc_option in ["params", "deps"]:
#                     return output
#                 else:
#                     # combine with the associated path, defined in pytrack.dvc
#                     file_path: Path = getattr(
#                         instance.pytrack.dvc, f"{self.pytrack_dvc_option}_path"
#                     )
#                     if isinstance(output, list):
#                         return [file_path / x for x in output]
#                     elif isinstance(output, str):
#                         return file_path / output
#                     else:
#                         return output
#
#     def __set__(self, instance: TypeHintParent, value):
#         """Update the value"""
#         try:
#             self._set(instance, value)
#         except NotImplementedError:
#             if self.pytrack_dvc_option != "result":
#                 self.check_input(value)
#
#             value = self.get_value(value)
#             if value is NoneType:
#                 return
#
#             log.debug(f"Updating {self.get_name(instance)} with {value}")
#
#             value = serializer(value)
#
#             self.set_internals(instance, {self.get_name(instance): value})
#
#     def _get(self, instance: TypeHintParent, owner):
#         """Overwrite this method for custom PyTrackOption get method"""
#         raise NotImplementedError
#
#     def _set(self, instance: TypeHintParent, value):
#         """Overwrite this method for custom PyTrackOption set method"""
#         raise NotImplementedError
#
#     def get_value(self, value):
#         """Get the value
#
#         If the input is a PyTrackOption gather the value trough the .value attribute
#         Otherwise if e.g. it is a pytrack stage, look for the results json file
#         and make that the resulting value
#
#         """
#         if isinstance(value, self.__class__):
#             value = value.value
#
#         # Check if the passed value is a PyTrack class
#         # if so, add its json file as a dependency to this stage.
#         if hasattr(value, "pytrack"):
#             # Allow self.deps = DVC.deps(Stage(id_=0))
#             if self.pytrack_dvc_option == "deps":
#                 new_value = value.pytrack.dvc.json_file
#                 if new_value is None:
#                     raise ValueError(f"Stage {value} has no results assigned to it!")
#                 else:
#                     value = new_value
#         return value
#
#     def get_name(self, instance):
#         """
#
#         Parameters
#         ----------
#         instance: TypeHintParent
#             A instance of the Parent that contains
#
#         Returns
#         -------
#         str: Name of this instance, e.g., self.abc = DVC.outs() returns "abc"
#
#         """
#         for attr, val in vars(type(instance)).items():
#             if val == self:
#                 return attr
#
#         raise ValueError(f"Could not find {self} in instance {instance}")
#
#     def check_input(self, value):
#         if isinstance(value, dict):
#             log.warning(
#                 f"Used mutable type dict for {self.pytrack_dvc_option}! "
#                 f"Always overwrite the {self.pytrack_dvc_option} and don't alter it "
#                 f"otherwise!, It won't work."
#             )
#
#         if isinstance(value, list):
#             log.warning(
#                 f"Used mutable type list for {self.pytrack_dvc_option}! "
#                 f"Always overwrite the {self.pytrack_dvc_option} and don't append "
#                 f"to it! It won't work."
#             )
#
#     def set_internals(self, instance: TypeHintParent, value: dict):
#         """Set the Internals for this instance (Stage & Id)
#
#         This writes them to self._pytrack_all_parameters, i.e., to the config file.
#         """
#         if isinstance(value, dict):
#             if self.pytrack_dvc_option == "result":
#                 if not instance.pytrack.allow_result_change:
#                     if instance.pytrack.is_init:
#                         log.debug("ValueError Exception during init!")
#                         return
#                     else:
#                         raise ValueError(
#                             "Result can only be changed within `run` call!"
#                         )
#                     # log.warning("Result can only be changed within `run` call!")
#                     # return
#                 if not is_jsonable(value):
#                     raise ValueError("Results must be JSON serializable")
#                 log.debug(f"Processing value {value}")
#                 results = self.get_results(instance)
#                 results.update(value)
#                 self.set_results(instance, results)
#
#             else:
#                 log.debug(
#                     f"Param_Change: {instance.pytrack.allow_param_change} on {instance.pytrack}"
#                 )
#                 if not instance.pytrack.allow_param_change:
#                     if instance.pytrack.is_init:
#                         log.debug("ValueError Exception during init!")
#                         return
#                     else:
#                         raise ValueError(
#                             "This stage is being loaded. Parameters can not be set!"
#                         )
#                 value = self.get_value(value)
#                 value = serializer(value)
#                 name = instance.pytrack.name
#                 id_ = instance.pytrack.id
#                 file = instance.pytrack.dvc.internals_file
#
#                 internals_from_file = self.get_full_internals(file)
#                 stage = internals_from_file.get(name, {})
#                 stage_w_id = stage.get(id_, {})
#
#                 option = stage_w_id.get(self.pytrack_dvc_option, {})
#                 option.update(value)
#
#                 stage_w_id[self.pytrack_dvc_option] = option
#                 stage[id_] = stage_w_id
#                 internals_from_file[name] = stage
#
#                 self.set_full_internals(file, internals_from_file)
#
#         else:
#             raise ValueError(
#                 f"Value has to be a dictionary but found {type(value)} instead!"
#             )
#
#     def get_internals(self, instance: TypeHintParent):
#         """Get the parameters for this instance (Stage & Id)"""
#         name = instance.pytrack.name
#         id_ = instance.pytrack.id
#         file = instance.pytrack.dvc.internals_file
#
#         internals_from_file = self.get_full_internals(file)
#
#         return (
#             internals_from_file.get(name, {}).get(id_, {}).get(self.pytrack_dvc_option, {})
#         )
#
#     @staticmethod
#     def get_full_internals(file) -> dict:
#         """Load ALL internals from .pytrack.json"""
#         try:
#             with open(file) as json_file:
#                 return json.load(json_file)
#         except FileNotFoundError:
#             log.debug(f"Could not load params from {file}!")
#         return {}
#
#     @staticmethod
#     def set_full_internals(file, value: dict):
#         """Update internals in .pytrack.json"""
#         log.debug(f"Writing updates to .pytrack.json as {value}")
#         value.update({"default": None})
#
#         if not is_jsonable(value):
#             raise ValueError(f"{value} is not JSON serializable")
#
#         Path(file).parent.mkdir(exist_ok=True, parents=True)
#
#         with open(file, "w") as json_file:
#             json.dump(value, json_file, indent=4)
#
#     @staticmethod
#     def get_results(instance: TypeHintParent):
#         file = instance.pytrack.dvc.json_file
#         try:
#             with open(file) as f:
#                 result = json.load(f)
#             log.debug(f"Loading results {result}")
#             return result
#         except FileNotFoundError:
#             log.warning("No results found!")
#             return {}
#
#     @staticmethod
#     def set_results(instance: TypeHintParent, value):
#         file = instance.pytrack.dvc.json_file
#         if not is_jsonable(value):
#             raise ValueError(f"{value} is not JSON serializable")
#         log.debug(f"Writing {value} to {file}")
#         with open(file, "w") as f:
#             json.dump(value, f, indent=4)
#         log.debug("successful!")
#
#     def __repr__(self):
#         return f"Descriptor for {self.pytrack_dvc_option}"
#
#
# class _DVC:
#     """Basically a dataclass of DVC methods
#
#     Referring to https://dvc.org/doc/command-reference/run#options
#     """
#
#     def __init__(self):
#         """Basically a dataclass of DVC methods"""
#         raise NotImplementedError(
#             "Cannot initialize DVC - this class is only for accessing its methods!"
#         )
#
#     @staticmethod
#     def params(value=NoneType):
#         """Parameter for PyTrack
#
#         Parameters
#         ----------
#         obj: any class object that the parameter will take on, so that type hinting does not raise issues
#
#         Returns
#         -------
#         cls: Class that inherits from obj
#
#         """
#
#         return PyTrackOption(value, option="params")
#
#     @staticmethod
#     def result(value=NoneType):
#         """Parameter for PyTrack
#
#         Parameters
#         ----------
#         obj: any class object that the parameter will take on, so that type hinting does not raise issues
#         outs: Future Version, allows for defining the type ot output
#
#         Returns
#         -------
#         cls: Class that inherits from obj
#
#         """
#
#         if value is not NoneType:
#             raise ValueError("Can not pre-initialize result!")
#
#         return PyTrackOption(value, option="result")
#
#     @staticmethod
#     def deps(value=NoneType):
#         return PyTrackOption(value, option="deps")
#
#     @staticmethod
#     def outs(value=NoneType):
#         return PyTrackOption(value, option="outs")
#
#     @staticmethod
#     def metrics_no_cache(value=NoneType):
#         return PyTrackOption(value, option="metrics_no_cache")
