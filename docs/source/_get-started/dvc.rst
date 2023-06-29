.. _userdoc-get-started-dvc:

.. _DVC: https://dvc.org/

Data Version Control
====================

Data Version Control (DVC_) is a fundamental building block of the ZnTrack package.
To learn more about DVC, please refer to the `DVC documentation <https://dvc.org/doc>`_.
DVC_ is responsible for keeping track of all the files and loading results from the cache if they are already available.

Why not just DVC?
-----------------

DVC_ provides all the tools necessary to build the workflows described in the previous section.
However, it is designed as a Command Line Tool.
With ZnTrack, you can build workflows more conveniently by using Python functions and classes directly.
This is especially useful for more complex workflows where code reuse and building more complex workflows are important.
Additionally, nodes written in ZnTrack can be easily shared with others and even pip installed (as we'll see in later sections).

..
  Write that section about pip installing zntrack nodes

DVC CLI
-------
When using ZnTrack, you'll often make extensive use of the DVC CLI.
Here are some of the most important commands:

- ``dvc init``: Initializes a DVC repository
- ``dvc repro``: Reproduces the pipeline
- ``dvc exp run``: Runs an experiment
- ``dvc checkout``: Checks out the results of the pipeline
- ``dvc push``: Pushes the results of the pipeline to a remote storage
