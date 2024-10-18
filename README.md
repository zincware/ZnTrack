[![coeralls](https://coveralls.io/repos/github/zincware/ZnTrack/badge.svg)](https://coveralls.io/github/zincware/ZnTrack)
[![codecov](https://codecov.io/gh/zincware/ZnTrack/branch/main/graph/badge.svg?token=ZQ67FXN1IT)](https://codecov.io/gh/zincware/ZnTrack)
[![Maintainability](https://api.codeclimate.com/v1/badges/f25e119bbd5d5ec74e2c/maintainability)](https://codeclimate.com/github/zincware/ZnTrack/maintainability)
![PyTest](https://github.com/zincware/ZnTrack/actions/workflows/test.yaml/badge.svg)
[![PyPI version](https://badge.fury.io/py/zntrack.svg)](https://badge.fury.io/py/zntrack)
[![code-style](https://img.shields.io/badge/code%20style-black-black)](https://github.com/psf/black/)
[![Documentation](https://readthedocs.org/projects/zntrack/badge/?version=latest)](https://zntrack.readthedocs.io/en/latest/?badge=latest)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/zincware/ZnTrack/HEAD)
[![DOI](https://img.shields.io/badge/arXiv-2401.10603-red)](https://arxiv.org/abs/2401.10603)
[![ZnTrack](https://img.shields.io/badge/Powered%20by-ZnTrack-%23007CB0)](https://zntrack.readthedocs.io/en/latest/)
[![zincware](https://img.shields.io/badge/Powered%20by-zincware-darkcyan)](https://github.com/zincware)

![Logo](https://raw.githubusercontent.com/zincware/ZnTrack/main/docs/source/_static/logo_ZnTrack.png)

# ZnTrack: A Parameter Tracking Package for Python

ZnTrack `zɪŋk træk` is a lightweight and easy-to-use package for tracking
parameters in your Python projects using DVC. With ZnTrack, you can define
parameters in Python classes and monitor how they change over time. This
information can then be used to compare the results of different runs, identify
computational bottlenecks, and avoid the re-running of code components where
parameters have not changed.

## Key Features

- Parameter, output and metric tracking: ZnTrack makes it easy to store and
  track the values of parameters in your Python code. It further allows you to
  store any outputs produced and gives an easy interface to define metrics.
- Lightweight and database-free: Unlike other parameter tracking solutions,
  ZnTrack is lightweight and does not require any databases.

## Getting Started

To get started with ZnTrack, you can install it via pip: `pip install zntrack`

Next, you can start using ZnTrack to track parameters, outputs and metrics in
your Python code. Here's an example of how to use ZnTrack to track the value of
a parameter in a Python class. Start in an empty directory and run `git init`
and `dvc init` for preparation.

Then put the following into a python file called `hello_world.py` and call it
with `python hello_world.py`.

```python
import zntrack
from random import randrange


class HelloWorld(zntrack.Node):
    """Define a ZnTrack Node"""
    # parameter to be tracked
    max_number: int = zntrack.params()
    # parameter to store as output
    random_number: int = zntrack.outs()

    def run(self):
        """Command to be run by DVC"""
        self.random_number = randrange(self.max_number)

if __name__ == "__main__":
    # Write the computational graph
    with zntrack.Project() as project:
        hello_world = HelloWorld(max_number=512)
    project.run()
```

This will create a [DVC](https://dvc.org) stage `HelloWorld`. The workflow is
defined in `dvc.yaml` and the parameters are stored in `params.yaml`.

This will run the workflow with `dvc repro` automatically. Once the graph is
executed, the results, i.e. the random number can be accessed directly by the
Node object.

```python
hello_world.load()
print(hello_world.random_number)
```

> ## Tip
>
> You can easily load a Node directly from a repository.
>
> ```python
> import zntrack
>
> node = zntrack.from_rev(
>     "ParamsToMetrics",
>     remote="https://github.com/PythonFZ/zntrack-examples",
>     rev="8d0c992"
> )
> ```
>
> Try accessing the `params` parameter and `metrics` output. All Nodes from this
> and many other repositories can be loaded like this.

An overview of all the ZnTrack features as well as more detailed examples can be
found in the [ZnTrack Documentation](https://zntrack.readthedocs.io/en/latest/).

## Wrap Python Functions

ZnTrack also provides tools to convert a Python function into a DVC Node. This
approach is much more lightweight compared to the class-based approach with only
a reduced set of functionality. Therefore, it is recommended for smaller nodes
that do not need the additional toolset that the class-based approach provides.

```python
from zntrack import nodify, NodeConfig
import pathlib

@nodify(outs=pathlib.Path("text.txt"), params={"text": "Lorem Ipsum"})
def write_text(cfg: NodeConfig):
    cfg.outs.write_text(
        cfg.params.text
    )
# build the DVC graph
with zntrack.Project() as project:
    write_text()
project.run()
```

The `cfg` dataclass passed to the function provides access to all configured
files and parameters via [dot4dict](https://github.com/zincware/dot4dict). The
function body will be executed by the `dvc repro` command or if ran via
`write_text(run=True)`. All parameters are loaded from or stored in
`params.yaml`.

# Technical Details

## ZnTrack as an Object-Relational Mapping for DVC

On a fundamental level the ZnTrack package provides an easy-to-use interface for
DVC directly from Python. It handles all the computational overhead of reading
config files, defining outputs in the `dvc.yaml` as well as in the script and
much more.

For more information on DVC visit their [homepage](https://dvc.org/doc).

# References

If you use ZnTrack in your research and find it helpful please cite us.

```bibtex
@misc{zillsZnTrackDataCode2024,
  title = {{{ZnTrack}} -- {{Data}} as {{Code}}},
  author = {Zills, Fabian and Sch{\"a}fer, Moritz and Tovey, Samuel and K{\"a}stner, Johannes and Holm, Christian},
  year = {2024},
  eprint={2401.10603},
  archivePrefix={arXiv},
}
```

# Copyright

This project is distributed under the
[Apache License Version 2.0](https://github.com/zincware/ZnTrack/blob/main/LICENSE).

## Similar Tools

The following (incomplete) list of other projects that either work together with
ZnTrack or can achieve similar results with slightly different goals or
programming languages.

- [DVC](https://dvc.org/) - Main dependency of ZnTrack for Data Version Control.
- [dvthis](https://github.com/jcpsantiago/dvthis) - Introduce DVC to R.
- [DAGsHub Client](https://github.com/DAGsHub/client) - Logging parameters from
  within .Python
- [MLFlow](https://mlflow.org/) - A Machine Learning Lifecycle Platform.
- [Metaflow](https://metaflow.org/) - A framework for real-life data science.
- [Hydra](https://hydra.cc/) - A framework for elegantly configuring complex
  applications
- [Snakemake](https://snakemake.readthedocs.io/en/stable/) - Workflow management
  system to create reproducible and scalable data analyses.
