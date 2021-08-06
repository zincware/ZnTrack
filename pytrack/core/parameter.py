"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: PyTrack parameter
"""

from pytrack.utils import is_jsonable
from pytrack.core.data_classes import DVCParams
from pathlib import Path


class ParameterHandler:
    def __init__(self):
        self.dvc_options = {}
        # save the attributes, e.g. {params: [param1, param2], results: [result1]}
        self.dvc_values = {}
        # save the actual values, e.g. {param1: value, param2, value, result1: value}

        self.dvc = DVCParams()

    def update_dvc_options(self, cls):
        for attr, value in vars(cls).items():
            try:
                self.update_dvc_internal(value.pytrack_dvc_option, attr)
            except AttributeError:  # not all attributes have an option
                pass

    def update_dvc(self, cls):
        """Save the user input"""
        for item in self.dvc_options:
            if item == "parameter":
                for option in self.dvc_options.get("parameter", []):
                    if is_jsonable(cls.__dict__[option]):
                        parameter_dict = self.dvc_values.get("parameter", {})
                        parameter_dict[option] = cls.__dict__[option]
                        self.dvc_values.update({"parameter": parameter_dict})
                    else:
                        raise ValueError(f'Parameter {parameter} is not json serializable!')
            if item == "result":
                # self.dvc is currently handled elsewhere!
                continue
            if item == "dependency":
                for option in self.dvc_options.get("dependency", []):
                    if isinstance(cls.__dict__[option], list):
                        raise NotImplementedError('Lists for dependencies are currently not implemented')
                    else:
                        self.dvc.deps.append(Path(cls.__dict__[option]))
            if item == "out":
                for option in self.dvc_options.get("out", []):
                    if isinstance(cls.__dict__[option], list):
                        raise NotImplementedError('Lists for dependencies are currently not implemented')
                    elif isinstance(cls.__dict__[option], PyTrackOption):
                        for abc in cls.__dict__[option].value:
                            print(abc)
                            self.dvc.outs.append(self.dvc.outs_path / abc)
                    else:
                        self.dvc.outs.append(self.dvc.outs_path / cls.__dict__[option])

    def update_dvc_internal(self, option, value):
        try:
            self.dvc_options[option].append(value)
        except KeyError:
            self.dvc_options[option] = [value]


class PyTrackOption:
    def __init__(self, option: str, value=None):
        if value is None:
            value = []
        self.pytrack_dvc_option = option
        self.value = value

    def __repr__(self):
        return f"Empty {self.pytrack_dvc_option}!"


def parameter(obj=object):
    """Parameter for PyTrack

    Parameters
    ----------
    obj: any class object that the parameter will take on, so that type hinting does not raise issues

    Returns
    -------
    cls: Class that inherits from obj

    """

    class PyTrackParameter(PyTrackOption, obj):
        pass

    return PyTrackParameter("parameter")


def result(obj=object):
    """Parameter for PyTrack

        Parameters
        ----------
        obj: any class object that the parameter will take on, so that type hinting does not raise issues
        outs: Future Version, allows for defining the type ot output

        Returns
        -------
        cls: Class that inherits from obj

        """

    class PyTrackParameter(PyTrackOption, obj):
        pass

    return PyTrackParameter("result")


def dependency(obj=object):
    class PyTrackParameter(PyTrackOption, obj):
        pass

    return PyTrackParameter("dependency")


def out(value=None, obj=object):
    class PyTrackParameter(PyTrackOption, obj):
        pass

    return PyTrackParameter("out", value=value)


DVC_PARAMS = {
    "deps": dependency,
    "outs": out
}

if __name__ == '__main__':
    class TEST:
        def __init__(self):
            self.param1 = parameter()
            self.param2 = parameter()
            self.out1 = out()
            self.result1 = result()

        def run(self):
            self.param1 = 10
            self.param2 = 20


    test = TEST()

    param_handler = ParameterHandler()

    param_handler.update_dvc_options(test)

    test.run()
    param_handler.update_dvc_parameters(test)

    print(param_handler.dvc_options)

    print(param_handler.dvc_values)
