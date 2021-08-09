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
from pytrack.core.data_classes import DVCParams
from pathlib import Path
from typing import Union, Dict, Any
from dataclasses import dataclass, field, asdict

log = logging.getLogger(__file__)

if typing.TYPE_CHECKING:
    from pytrack.core.py_track import PyTrackParent


@dataclass
class DVCValues:
    parameter: Dict[str, Any] = field(default_factory=dict)
    deps: Dict[str, Any] = field(default_factory=dict)
    outs: Dict[str, Any] = field(default_factory=dict)
    result: Dict[str, Any] = field(default_factory=dict)  # check what this is?!


class ParameterHandler:
    def __init__(self):
        # TODO remove dvc_options and only use dvc_values
        self.dvc_options = DVCValues()
        # save the attributes, e.g. {params: [param1, param2], results: [result1]}
        self.dvc_values = DVCValues()  # see dataclass definition

        self.dvc = DVCParams()

    def update_dvc_options(self, cls):
        """Update the dvc_options with None values

        This is run after the __init__ to save all DVCParams and they can later be overwritten
        """
        for attr, value in vars(cls).items():
            try:
                option = value.pytrack_dvc_option
                try:
                    setattr(type(cls), attr, PyTrackOption(option=option, value=value.value, attr=attr, cls=cls))
                    log.debug(f"Updating {attr} with PyTrackOption and value {value.value}!")
                except AttributeError:
                    raise AttributeError('setattr went wrong!')
            except AttributeError:
                pass

        # assumes all DVC.<placeholder> are converted to descriptors
        for attr, value in vars(type(cls)).items():
            try:
                option = value.pytrack_dvc_option
                try:
                    getattr(self.dvc_options, option).update({attr: None})
                except AttributeError:
                    log.warning(f"Could not set attr {option}!")
            except AttributeError:  # not all attributes have an pytrack_dvc_option
                pass

    def update_dvc(self, cls):
        """Save the user input"""
        for option in self.dvc_options.parameter:
            if is_jsonable(getattr(cls, option)):
                parameter_dict = self.dvc_values.parameter
                parameter_dict[option] = getattr(cls, option)
                self.dvc_values.parameter.update(parameter_dict)
            else:
                raise ValueError(f'Parameter {option} is not json serializable! ({getattr(cls, option)})')

        for option in asdict(self.dvc_options):
            if option == "parameter":
                continue
            if option == "result":
                continue
            for value in getattr(self.dvc_options, option):
                getattr(self.dvc_values, option).update({value: getattr(cls, value)})

            self.update_cls_attributes(option, cls)

    def update_cls_attributes(self, item, cls):
        """

        Parameters
        ----------
        item: the dvc option item to update
        cls: the class to get the attributes from
        target: the target, e.g. DVCParams.deps
        path: (optional) the standard path, e.g. DVCParams.outs_path

        Returns
        -------

        """

        target = getattr(self.dvc, item)
        try:
            path = getattr(self.dvc, f'{item}_path')
        except AttributeError:
            path = Path()

        for option in getattr(self.dvc_options, item):
            if isinstance(getattr(cls, option), tuple):
                # raise NotImplementedError('Lists are not yet supported!')
                # if self.param = ["a", "b"]
                for abc in getattr(cls, option):
                    target.append(path / abc)
            elif isinstance(getattr(cls, option), PyTrackOption):
                if isinstance(getattr(cls, option), tuple):
                    # raise NotImplementedError('Lists are not yet supported!')
                    # if self.param = DVC.outs(["a", "b"])
                    for abc in getattr(cls, option):
                        target.append(path / abc)
                else:
                    # if self.param = DVC.outs("a")
                    target.append(path / getattr(cls, option))
            else:
                # if self.param = "a"
                target.append(path / getattr(cls, option))


class PyTrackOption:
    def __init__(self, option: str, value: Union[str, tuple] = None, attr: str = None, cls: PyTrackParent = None):
        self.check_input(value)

        self.pytrack_dvc_option = option

        self.value = value
        if value is not None and cls is not None:
            self.set_internals(cls, {attr: value})

    def __get__(self, instance: PyTrackParent, owner):
        """Get the value of this instance from pytrack_internals and return it"""
        output = self.get_internals(instance).get(self.get_name(instance))
        if isinstance(output, list):
            return tuple(output)  # json reads lists, we want a tuple at all time to avoid appending to it
        else:
            return output

    def __set__(self, instance: PyTrackParent, value):
        """Update the value"""
        self.check_input(value)
        log.debug(f"Updating {self.get_name(instance)} with {value}")
        self.set_internals(instance, {self.get_name(instance): value})

    def get_name(self, instance):
        """

        Parameters
        ----------
        instance: PyTrackParent
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
            raise ValueError(f'Value {value} must be immutable. Please use tuple,'
                             f' or non-iterable types instead of dict!')

        if isinstance(value, list):
            raise ValueError(f"Value {value} must be immutable. Please convert list to tuple!")

    def set_internals(self, instance: PyTrackParent, value: dict):
        """Set the Internals for this instance (Stage & Id)

        This writes them to self._pytrack_all_parameters, i.e., to the config file.
        """
        if isinstance(value, dict):
            name = instance._pytrack_name
            id_ = instance._pytrack_id
            file = instance._pytrack_ph.dvc.internals_file

            full_internals = self.get_full_internals(file)

            stage = full_internals.get(name, {}).get(id_, {})
            option = stage.get(self.pytrack_dvc_option, {})
            option.update(value)
            stage[self.pytrack_dvc_option] = option

            self.set_full_internals(file, {name: {id_: stage}})

        else:
            raise ValueError(
                f"Value has to be a dictionary but found {type(value)} instead!"
            )

    def get_internals(self, instance: PyTrackParent):
        """Get the parameters for this instance (Stage & Id)"""
        name = instance._pytrack_name
        id_ = instance._pytrack_id
        file = instance._pytrack_ph.dvc.internals_file

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
        log.debug(f"Writing updates to .pytrack.json as {value}")
        value.update({"default": None})

        Path(file).parent.mkdir(exist_ok=True, parents=True)

        with open(file, "w") as json_file:
            json.dump(value, json_file, indent=4)

    def __repr__(self):
        return f"Descriptor for {self.pytrack_dvc_option}"


class DVC:
    """Basically a dataclass of DVC methods"""

    def __init__(self):
        """Basically a dataclass of DVC methods"""
        raise NotImplementedError('Can not initialize DVC - this class is purely for accessing its methods!')

    @staticmethod
    def parameter(value=None):
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

        return PyTrackParameter("parameter", value=value)

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


if __name__ == '__main__':
    class TEST:
        def __init__(self):
            self.param1 = DVC.parameter()
            self.param2 = DVC.parameter()
            self.out1 = DVC.outs()
            self.result1 = DVC.result()

        def run(self):
            self.param1 = 10
            self.param2 = 20


    test = TEST()

    param_handler = ParameterHandler()

    param_handler.update_dvc_options(test)

    test.run()
    param_handler.update_dvc(test)

    print(param_handler.dvc_options)

    print(param_handler.dvc_values)
