[![coeralls](https://coveralls.io/repos/github/zincware/ZnTrack/badge.svg)](https://coveralls.io/github/zincware/ZnTrack)
[![codecov](https://codecov.io/gh/zincware/ZnTrack/branch/main/graph/badge.svg?token=ZQ67FXN1IT)](https://codecov.io/gh/zincware/ZnTrack)
[![Maintainability](https://api.codeclimate.com/v1/badges/f25e119bbd5d5ec74e2c/maintainability)](https://codeclimate.com/github/zincware/ZnTrack/maintainability)
![PyTest](https://github.com/zincware/ZnTrack/actions/workflows/pytest.yaml/badge.svg)
[![PyPI version](https://badge.fury.io/py/zntrack.svg)](https://badge.fury.io/py/zntrack)
[![code-style](https://img.shields.io/badge/code%20style-black-black)](https://github.com/psf/black/)
[![Documentation](https://readthedocs.org/projects/zntrack/badge/?version=latest)](https://zntrack.readthedocs.io/en/latest/?badge=latest)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/zincware/ZnTrack/HEAD)

![Logo](https://raw.githubusercontent.com/zincware/ZnTrack/main/docs/source/img/zntrack.png)

# Parameter Tracking for Python

ZnTrack [zɪŋk træk] is an easy-to-use package for tracking parameters and creating computational graphs for your Python
projects.
What is a parameter? Anything set by a user in your code, for example, the number of
layers in a neural network or the window size of a moving average.
ZnTrack works by storing the values of parameters in Python classes and functions and
monitoring how they change for several different runs.
These changes can then be compared graphically to see what effect they had on your
workflow.
Beyond the standard tracking of parameters in a project, ZnTrack can be used to deploy
jobs with a set of different parameter values, avoid the re-running of code components
where parameters have not changed, and to identify computational bottlenecks.

## Example
ZnTrack is based on [DVC](https://dvc.org).
With ZnTrack a DVC Node on the computational graph can be written as a Python class.
DVC Options, such as parameters, input dependencies and output files are defined as class attributes.

The following example shows a Node to compute a random number between 0 and a user defined maximum.

````python
from zntrack import Node, zn
from random import randrange


class HelloWorld(Node):
    """Define a ZnTrack Node"""
    # parameter to be tracked
    max_number: int = zn.params()
    # parameter to store as output
    random_number: int = zn.outs()
    
    def run(self):
        """Command to be run by DVC"""
        self.random_number = randrange(self.max_number)
````

This Node can then be put on the computational graph (writing the `dvc.yaml` and `params.yaml` files) by calling `write_graph()`. 
The graph can then be executed e.g., through `dvc repro`.

````python
HelloWorld(max_number=512).write_graph()
````    

Once `dvc repro` is called, the results, i.e. the random number can be accessed directly by the Node object.
```python
hello_world = HelloWorld.load()
print(hello_world.random_numer)
```
An overview of all the ZnTrack features as well as more detailed examples can be found in the [ZnTrack Documentation](https://zntrack.readthedocs.io/en/latest/).

## Wrap Python Functions
ZnTrack also provides tools to convert a Python function into a DVC Node.
This approach is much more lightweight compared to the class-based approach with only a reduced set of functionality.
Therefore, it is recommended for smaller nodes that do not need the additional toolset that the class-based approach provides.

````python
from zntrack import nodify, NodeConfig
import pathlib

@nodify(outs=pathlib.Path("text.txt"), params={"text": "Lorem Ipsum"})
def write_text(cfg: NodeConfig):
    cfg.outs.write_text(
        cfg.params.text
    )
# build the DVC graph
write_text()
````

The ``cfg`` dataclass passed to the function provides access to all configured files
and parameters via [dot4dict](https://github.com/zincware/dot4dict). The function body
will be executed by the ``dvc repro`` command or if ran via `write_text(run=True)`.
All parameters are loaded from or stored in ``params.yaml``.

# Technical Details


## ZnTrack as an Object-Relational Mapping for DVC

On a fundamental level the ZnTrack package provides an easy-to-use interface for DVC directly from Python.
It handles all the computational overhead of reading config files, defining outputs in the `dvc.yaml` as well as in the script and much more.

For more information on DVC visit their [homepage](https://dvc.org/doc).


Installation
============

Install the stable version from PyPi via

````shell
pip install zntrack
```` 

or install the latest development version from source with:

````shell
git clone https://github.com/zincware/ZnTrack.git
cd ZnTrack
pip install .
````

Copyright
=========

This project is distributed under the [Apache License Version 2.0](https://github.com/zincware/ZnTrack/blob/main/LICENSE).

## Similar Tools
The following (incomplete) list of other projects that either work together with ZnTrack or can achieve similar results with slightly different goals or programming languages.

- [DVC](https://dvc.org/) - Main dependency of ZnTrack for Data Version Control.
- [dvthis](https://github.com/jcpsantiago/dvthis) - Introduce DVC to R.
- [DAGsHub Client](https://github.com/DAGsHub/client) - Logging parameters from within .Python 
- [MLFlow](https://mlflow.org/) - A Machine Learning Lifecycle Platform.
- [Metaflow](https://metaflow.org/) - A framework for real-life data science.
- [Hydra](https://hydra.cc/) - A framework for elegantly configuring complex applications
