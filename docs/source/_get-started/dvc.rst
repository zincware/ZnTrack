.. _userdoc-get-started-dvc:

.. _DVC: https://dvc.org/

Data Version Control
====================

The Data Version Control (DVC_) package is the fundamental building block of the ZnTrack package.
For detailed information on DVC, please refer to the `DVC documentation <https://dvc.org/doc>`_.
DVC_ will keep track of all the files and load results from the cache, if they are already available.

Why not just DVC?
-----------------

The DVC_ package provides all the tools to build the workflows described in the previous section.
However, DVC_ is designed as a Command Line Tool.
With ZnTrack you can build the workflows in a more convenient way, using Python functions and classes directly.
This is especially useful for more complex workflows, where you want to reuse code and build more complex workflows.
Also, Nodes written in ZnTrack can be easily shared with others or even pip installed (see later sections).

DVC CLI
-------
When using ZnTrack one will often make extensive use of the DVC CLI.
Therefore, here are some of the most important commands:

- ``dvc init``: Initialize a DVC repository
- ``dvc repro``: Reproduce the pipeline
- ``dvc exp run``: Run an experiment
- ``dvc checkout``: Checkout the results of the pipeline
- ``dvc push``: Push the results of the pipeline to a remote storage



