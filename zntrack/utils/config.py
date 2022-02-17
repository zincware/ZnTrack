"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: Configuration File for ZnTrack
"""
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    """Collection of Node configurations

    Attributes
    ----------
    nb_name: str
        Name of the JupyterNotebook, if the Nodes are defined in a Notebook
    nb_class_path: Path
        The path where jupyter notebooks should write the *.py
    lazy: bool, default = True
        Use lazy loading for Node.load(). This means that all ZnTrackOptions are only
        loaded from files when they are first accessed.
    """

    nb_name: str = None
    nb_class_path: Path = Path("src")
    lazy: bool = True


@dataclass(frozen=True)
class Files:
    """Important File paths for ZnTrack to work

    Notes
    ------
    Currently frozen because changing the value is not tested.
    """

    zntrack: Path = Path("zntrack.json")
    params: Path = Path("params.yaml")


@dataclass(frozen=True)
class ZnTypes:
    """Collection of ZnTrack Types to identify descriptors beyond their dvc option

    Attributes
    ----------
    results: most zn.<options> like zn.outs() / zn.metrics() use this one
    """

    deps: str = "deps"
    dvc: str = "dvc"
    metadata: str = "metadata"
    method: str = "method"
    params: str = "params"
    iterable: str = "iterable"
    results: str = "results"


config = Config()
