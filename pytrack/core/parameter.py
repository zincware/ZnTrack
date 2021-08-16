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

import json
from pytrack.utils import is_jsonable
from pathlib import Path
from typing import Union

log = logging.getLogger(__file__)

if typing.TYPE_CHECKING:
    from pytrack.core.py_track import PyTrackParent
    from pytrack.utils.type_hints import TypeHintParent


class PyTrackOption:
    def __init__(self, option: str, value: Union[str, tuple] = None, attr: str = None, cls: TypeHintParent = None):
        """PyTrack Descriptor to handle the loading and writing of files

        Parameters
        ----------
        option
        value
        attr
        cls
        """
        self.pytrack_dvc_option = option
        self.value = value
        self.check_input(value)
        if value is not None and cls is not None:
            value = self.make_serializable(value)
            self.set_internals(cls, {attr: value})

    def __get__(self, instance: TypeHintParent, owner):
        """Get the value of this instance from pytrack_internals and return it"""
        if self.pytrack_dvc_option == "result":
            return self.get_results(instance).get(self.get_name(instance))
        else:
            output = self.get_internals(instance).get(self.get_name(instance), "")
            if self.pytrack_dvc_option == "params":
                return output
            elif self.pytrack_dvc_option == "deps":
                if isinstance(output, list):
                    return [Path(x) for x in output]
                else:
                    return Path(output)
            else:
                # convert to path
                file_path: Path = getattr(instance.pytrack.dvc, f"{self.pytrack_dvc_option}_path")
                if isinstance(output, list):
                    return [file_path / x for x in output]
                elif isinstance(output, str):
                    return file_path / output
                else:
                    return output

    def __set__(self, instance: TypeHintParent, value):
        # TODO support Path objects and lists of Path objects!
        # TODO support dicts for parameters and write them to a different file?!
        """Update the value"""
        if self.pytrack_dvc_option != "result":
            self.check_input(value)
        log.warning(f"Updating {self.get_name(instance)} with {value}")

        value = self.make_serializable(value)

        self.set_internals(instance, {self.get_name(instance): value})

    def make_serializable(self, value):
        """Make value serializable to save as json"""
        if isinstance(value, self.__class__):
            value = value.value

        if hasattr(value, "pytrack"):
            # Allow self.deps = DVC.deps(Stage(id_=0))
            if self.pytrack_dvc_option == "deps":
                new_value = value.pytrack.dvc.json_file
                if new_value is None:
                    raise ValueError(f"Stage {value} has no results assigned to it!")
                else:
                    value = new_value

        if isinstance(value, Path):
            value = value.as_posix()

        def conv_path_lists(path_list):
            if isinstance(path_list, list):
                str_list = []
                for entry in path_list:
                    if isinstance(entry, Path):
                        str_list.append(entry.as_posix())
                    else:
                        str_list.append(entry)
                return str_list
            return path_list

        def conv_path_dict(path_dict):
            if isinstance(path_dict, dict):
                str_dict = {}
                for key, val in path_dict.items():
                    if isinstance(val, Path):
                        str_dict[key] = val.as_posix()
                    else:
                        str_dict[key] = conv_path_lists(val)
                return str_dict
            return path_dict

        value = conv_path_lists(value)
        value = conv_path_dict(value)

        return value

    def get_name(self, instance):
        """

        Parameters
        ----------
        instance: TypeHintParent
            A instance of the Parent that contains

        Returns
        -------
        str: Name of this instance, e.g., self.abc = DVC.outs() returns "abc"

        """
        for attr, val in vars(type(instance)).items():
            if val == self:
                return attr

        raise ValueError(f'Could not find {self} in instance {instance}')

    def check_input(self, value):
        if isinstance(value, dict):
            log.warning(f"Used mutable type dict for {self.pytrack_dvc_option}! "
                        f"Always overwrite the {self.pytrack_dvc_option} and don't alter it otherwise!"
                        f" It won't work.")

        if isinstance(value, list):
            log.warning(f"Used mutable type list for {self.pytrack_dvc_option}! "
                        f"Always overwrite the {self.pytrack_dvc_option} and don't append to it!"
                        f" It won't work.")

    def set_internals(self, instance: TypeHintParent, value: dict):
        """Set the Internals for this instance (Stage & Id)

        This writes them to self._pytrack_all_parameters, i.e., to the config file.
        """
        if isinstance(value, dict):
            if self.pytrack_dvc_option == "result":
                if not instance.pytrack.allow_result_change:
                    log.warning("Result can only be changed within `run` call!")
                    return
                if not is_jsonable(value):
                    raise ValueError('Results must be JSON serializable')
                log.warning(f"Processing value {value}")
                results = self.get_results(instance)
                results.update(value)
                self.set_results(instance, results)

            else:
                log.warning(f"Param_Change: {instance.pytrack.allow_param_change} on {instance.pytrack}")
                if not instance.pytrack.allow_param_change:
                    log.warning("This stage is being loaded. No internals will be changed!")
                    return
                value = self.make_serializable(value)
                name = instance.pytrack.name
                id_ = instance.pytrack.id
                file = instance.pytrack.dvc.internals_file

                full_internals = self.get_full_internals(file)
                stage = full_internals.get(name, {})
                stage_w_id = stage.get(id_, {})

                option = stage_w_id.get(self.pytrack_dvc_option, {})
                option.update(value)

                stage_w_id[self.pytrack_dvc_option] = option
                stage[id_] = stage_w_id
                full_internals[name] = stage

                self.set_full_internals(file, full_internals)

        else:
            raise ValueError(
                f"Value has to be a dictionary but found {type(value)} instead!"
            )

    def get_internals(self, instance: TypeHintParent):
        """Get the parameters for this instance (Stage & Id)"""
        name = instance.pytrack.name
        id_ = instance.pytrack.id
        file = instance.pytrack.dvc.internals_file

        full_internals = self.get_full_internals(file)

        return full_internals.get(name, {}).get(id_, {}).get(self.pytrack_dvc_option, {})

    @staticmethod
    def get_full_internals(file) -> dict:
        """Load ALL internals from .pytrack.json"""
        try:
            with open(file) as json_file:
                return json.load(json_file)
        except FileNotFoundError:
            log.debug(
                f"Could not load params from {file}!"
            )
        return {}

    @staticmethod
    def set_full_internals(file, value: dict):
        """Update internals in .pytrack.json"""
        log.warning(f"Writing updates to .pytrack.json as {value}")
        value.update({"default": None})

        if not is_jsonable(value):
            raise ValueError(f'{value} is not JSON serializable')

        Path(file).parent.mkdir(exist_ok=True, parents=True)

        with open(file, "w") as json_file:
            json.dump(value, json_file, indent=4)

    @staticmethod
    def get_results(instance: TypeHintParent):
        file = instance.pytrack.dvc.json_file
        try:
            with open(file) as f:
                result = json.load(f)
            log.warning(f"Loading results {result}")
            return result
        except FileNotFoundError:
            log.warning("No results found!")
            return {}

    @staticmethod
    def set_results(instance: TypeHintParent, value):
        file = instance.pytrack.dvc.json_file
        if not is_jsonable(value):
            raise ValueError(f'{value} is not JSON serializable')
        log.warning(f"Writing {value} to {file}")
        with open(file, "w") as f:
            json.dump(value, f, indent=4)
        log.warning("successful!")

    def __repr__(self):
        return f"Descriptor for {self.pytrack_dvc_option}"


class DVC:
    """Basically a dataclass of DVC methods"""

    def __init__(self):
        """Basically a dataclass of DVC methods"""
        raise NotImplementedError('Can not initialize DVC - this class is purely for accessing its methods!')

    @staticmethod
    def params(value=None):
        """Parameter for PyTrack

        Parameters
        ----------
        obj: any class object that the parameter will take on, so that type hinting does not raise issues

        Returns
        -------
        cls: Class that inherits from obj

        """

        class PyTrackParameter(PyTrackOption):
            pass

        return PyTrackParameter("params", value=value)

    @staticmethod
    def result(value=None):
        """Parameter for PyTrack

            Parameters
            ----------
            obj: any class object that the parameter will take on, so that type hinting does not raise issues
            outs: Future Version, allows for defining the type ot output

            Returns
            -------
            cls: Class that inherits from obj

            """

        if value is not None:
            raise ValueError('Can not pre-initialize result!')

        class PyTrackParameter(PyTrackOption):
            pass

        return PyTrackParameter("result", value=value)

    @staticmethod
    def deps(value=None):
        class PyTrackParameter(PyTrackOption):
            pass

        return PyTrackParameter("deps", value=value)

    @staticmethod
    def outs(value=None):
        class PyTrackParameter(PyTrackOption):
            pass

        return PyTrackParameter("outs", value=value)
