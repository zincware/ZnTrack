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
from typing import Union


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
                    if isinstance(getattr(cls, option), Path):
                        # Convert Path -> string
                        setattr(cls, option, getattr(cls, option).as_posix())
                    if is_jsonable(getattr(cls, option)):
                        parameter_dict = self.dvc_values.get("parameter", {})
                        parameter_dict[option] = getattr(cls, option)
                        self.dvc_values.update({"parameter": parameter_dict})
                    else:
                        raise ValueError(f'Parameter {option} is not json serializable!')
            if item == "result":
                # self.dvc is currently handled elsewhere!
                continue
            if item == "deps":
                self.update_cls_attributes(item, cls, self.dvc.deps)
            if item == "outs":
                self.dvc.outs_path.mkdir(parents=True, exist_ok=True)
                self.update_cls_attributes(item, cls, self.dvc.outs, self.dvc.outs_path)

    def update_cls_attributes(self, item, cls, target, path=Path()):
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
        for option in self.dvc_options.get(item, []):
            if isinstance(getattr(cls, option), list):
                raise NotImplementedError('Lists are not yet supported!')
                # if self.param = ["a", "b"]
                # for abc in getattr(cls, option):
                #     target.append(path / abc)
            elif isinstance(getattr(cls, option), PyTrackOption):
                if isinstance(getattr(cls, option).value, list):
                    raise NotImplementedError('Lists are not yet supported!')
                    # if self.param = DVC.outs(["a", "b"])
                    # for abc in getattr(cls, option).value:
                    #     target.append(path / abc)
                else:
                    # if self.param = DVC.outs("a")
                    target.append(path / getattr(cls, option).value)
            else:
                # if self.param = "a"
                target.append(path / getattr(cls, option))

    def update_dvc_internal(self, option, value):
        try:
            self.dvc_options[option].append(value)
        except KeyError:
            self.dvc_options[option] = [value]


class PyTrackOption:
    def __init__(self, option: str, value: Union[list, str] = None):
        if value is None:
            value = []
        self.pytrack_dvc_option = option
        self.value = value

    def __repr__(self):
        return f"Empty {self.pytrack_dvc_option}!"


class DVC:

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def deps(value=None, obj=object):
        class PyTrackParameter(PyTrackOption, obj):
            pass

        return PyTrackParameter("deps", value=value)

    @staticmethod
    def outs(value=None, obj=object):
        class PyTrackParameter(PyTrackOption, obj):
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
