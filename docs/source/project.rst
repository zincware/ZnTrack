.. _project:

Project
=======

A workflow is defined within a :term:`Project`.

To create a new ZnTrack project, initialize a new repository:

.. tip::

    ZnTrack builds a :term:`DVC` data pipeline for you.
    You don't need to know :term:`DVC` to use ZnTrack, but it is recommended to familiarize yourself with the basics.
    For more information, see the `DVC documentation <https://dvc.org/doc/start/data-pipelines/data-pipelines>`_ on data pipelines.

.. code-block:: bash

    mkdir my_project
    cd my_project
    git init
    dvc init

.. note::

    This documentation assumes that you have a single workflow file, ``main.py``, in the root of your project.
    Additionally, all :term:`Node` definitions that do not originate from a package should be imported from ``src/__init__.py``.

    To ensure this structure, run:

    .. code-block:: bash

        touch main.py
        mkdir src
        touch src/__init__.py


.. dropdown:: Available Nodes

    This project uses the following Node definitions in ``src/__init__.py``:

    .. code-block:: python

            import zntrack

            class Add(zntrack.Node):
                a: int = zntrack.params()
                b: int = zntrack.params()

                result: int = zntrack.outs()

                def run(self) -> None:
                    self.result = self.a + self.b

            # Multiply uses ``zntrack.deps`` to process data from other nodes
            class Multiply(zntrack.Node):
                a: int = zntrack.deps()
                b: int = zntrack.deps()

                result: int = zntrack.outs()

                def run(self) -> None:
                    self.result = self.a * self.b

We will now define a workflow that connects multiple :term:`Node` instances.
As you can see, ZnTrack allows you to connect Nodes directly through their attributes.
It is important to treat the ``main.py`` file purely as a workflow configuration file.
For a great explanation of this approach, refer to the `Apache Airflow documentation <https://airflow.apache.org/docs/apache-airflow/stable/tutorial/fundamentals.html#it-s-a-dag-definition-file>`_.


.. note::

    In addition to the predefined fields (e.g., ``a``, ``b``, and ``result``), it is also possible to pass the full :term:`Node` instance as an argument.
    For on-the-fly computations, you can define ``@property`` methods that are not stored in the :term:`Node` state and pass them between :term:`Node` instances.
    The ``@property`` decorator can also be used to define custom file readers.


.. dropdown:: The Project Context Manager

    The workflow is defined within the context manager of the :term:`Project`.
    Instead of passing actual values, a :term:`ZnFlow` connection is created between :term:`Node` instances.
    However, a :term:`Node` can also be used like a regular Python object outside of the context manager.

.. code-block:: python

    import zntrack

    from src import Add, Multiply

    project = zntrack.Project()

    with project:
        add1 = Add(a=1, b=2)
        add2 = Add(a=3, b=4)
        add3 = Multiply(a=add1.result, b=add2.result)

    project.build()

Calling ``project.build()`` generates all necessary configuration files and prepares the project for execution.


.. dropdown:: ZnTrack Configuration Files
    :open:

    A ZnTrack project typically consists of three configuration files:

    - ``params.yaml``: Stores parameters defined in ``main.py``, organized by :term:`node name` keys.
    - ``dvc.yaml``: Defines the :term:`DVC` workflow. For details, see the `DVC documentation <https://dvc.org/doc/user-guide/project-structure/dvcyaml-files#dvcyaml>`_.
    - ``zntrack.json``: Contains additional metadata used by ZnTrack to manage the workflow.

    You should not modify ``dvc.yaml`` or ``zntrack.json`` manually.
    While you can edit ``params.yaml``, it is recommended to change parameters within ``main.py`` to maintain a single source of truth.

To execute the workflow, use the ``dvc`` command-line tool:

.. code-block:: bash

    dvc repro

.. tip::

    Instead of running ``dvc repro``, you can call ``project.repro()`` instead of ``project.build()``.


Groups
------

To organize the workflow, you can group :term:`Node` instances.
Groups are purely for organization and do not affect execution.

.. note::

    Each :term:`Node` is assigned a unique name.
    By default, this name consists of the class name followed by a counter.
    If a :term:`Node` is part of a group, the group name is prefixed to its name.

    You can list all :term:`Node` names using the CLI command ``zntrack list``.
    If you want to set a custom name, pass the ``name`` argument when creating the :term:`Node` instance:

    .. code-block:: python

        add1 = Add(a=1, b=2, name="custom_name")

    If a :term:`Node` is in a group, the group name is also prefixed to the custom name.
    Custom names must be unique within their group.
    If a duplicate name is found, ZnTrack will raise an error.


.. code-block:: python

    project = zntrack.Project()

    with project:
        add1 = Add(a=1, b=2)
        print(add1.name)
        >>> Add

    with project.group("grp"):
        add2 = Add(a=1, b=2)
        print(add2.name)
        >>> grp_Add

    with project.group("grp", "subgrp"):
        add3 = Add(a=3, b=4)
        print(add3.name)
        >>> grp_subgrp_Add

    project.build()

MLFlow Integration
------------------

ZnTrack provides an integration between DVC and MLFlow.
You can upload existing runs using a command line interface if mlflow is installed.
See the CLI help for information on how to configure the MLFlow server, selected :term:`Node` instances, and the experiment id.

.. code-block:: bash

    zntrack mlflow-sync --help
