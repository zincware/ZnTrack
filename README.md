[![coeralls](https://coveralls.io/repos/github/zincware/ZnTrack/badge.svg)](https://coveralls.io/github/zincware/ZnTrack)
![PyTest](https://github.com/zincware/ZnTrack/actions/workflows/pytest.yaml/badge.svg)
[![PyPI version](https://badge.fury.io/py/zntrack.svg)](https://badge.fury.io/py/zntrack)
[![License](https://img.shields.io/badge/License-EPL-purple.svg?style=flat)](https://www.eclipse.org/legal/epl-2.0/faq.php)
[![code-style](https://img.shields.io/badge/code%20style-black-black)](https://github.com/psf/black/)
[![Documentation](https://readthedocs.org/projects/zntrack/badge/?version=latest)](https://zntrack.readthedocs.io/en/latest/?badge=latest)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/zincware/ZnTrack/HEAD)

![Logo](https://raw.githubusercontent.com/zincware/ZnTrack/main/docs/source/img/zntrack.png)

# Parameter Tracking for Python

ZnTrack [zɪŋk træk] is an easy-to-use package for tracking parameters in your Python
projects.
What is a parameter? Anything set by a user in your code, for example, the number of
layers in a neural network layer or the window size of a moving average.
ZnTrack works by storing the values of parameters in Python classes and functions and
monitoring how they change for several different runs.
These changes can then be compared graphically to see what effect they had on your
workflow.
Beyond the standard tracking of parameters in a project, ZnTrack can be used to deploy
jobs with a set of different parameter values, avoid the re-running of components of code
where parameters have not changed, and to identify computational bottlenecks in your
code.

## Example

With ZnTrack a DVC Node on the computational graph can be written as a Python class.
DVC Options, such as parameters, input dependencies and output files are class attributes.

````python
from zntrack import Node, zn
from random import randrange


class HelloWorld(Node):
    """Define a ZnTrack Node"""
    # parameter to be tracked
    max_number = zn.params()
    # parameter to store as output
    random_number = zn.outs()

    def __init__(self, max_number=None, *args, **kwargs):
        """Pass tracked arguments"""
        super().__init__(*args, **kwargs)
        self.max_number = max_number

    def run(self):
        """Command to be run by DVC"""
        self.random_number = randrange(self.max_number)
````


This Node can then be saved as a DVC stage

````python
HelloWorld(max_number=512).write_graph()
````

    

which builds the DVC stage and can be used e.g., through `dvc repro`.
The results can then be accessed easily via `HelloWorld.load().random_number`.

More detailed examples and further information can be found in the [ZnTrack Documentation](https://zntrack.readthedocs.io/en/latest/).

# Technical Details


## ZnTrack as an Object-Relational Mapping for DVC

On a fundamental level the ZnTrack package provides an easy-to-use interface for DVC directly from Python.
It handles all the computational overhead of reading config files, defining outputs in the `dvc.yaml` as well as in the script and much more.

For more information on DVC visit their [homepage](https://dvc.org/doc).


Installation
============

Simply run:

````shell
pip install zntrack
```` 

Or you can install from source with:

````shell
git clone https://github.com/zincware/ZnTrack.git
cd ZnTrack
pip install .
````

## Similar Tools
The following (incomplete) list of other projects that either work together with ZnTrack or can achieve similar results with slightly different goals or programming languages.

- [DVC](https://dvc.org/) - Main dependency of ZnTrack for Data Version Control.
- [dvthis](https://github.com/jcpsantiago/dvthis) - Introduce DVC to R.
- [DAGsHub Client](https://github.com/DAGsHub/client) - Logging parameters from within .Python 
- [MLFlow](https://mlflow.org/) - A Machine Learning Lifecycle Platform.
- [Metaflow](https://metaflow.org/) - A framework for real-life data science.
