.. _project:

Project
=======

A workflow is defined within a :term:`Project`.

To create a new ZnTrack Project, create a new repository.

.. code-block:: bash

    mkdir my_project
    cd my_project
    git init
    dvc init

.. note::

    This documentation assumes that you have one workflow file ``main.py`` in the root of your project.
    Further all :term:`Node` definitions that do not originate from a package are expected to be imported from ``src/__init__.py``.

    To ensure this, you can also run

    .. code-block :: python

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

            # Multiply used ``zntrack.deps`` to process data from other nodes
            class Multiply(zntrack.Node):
                a: int = zntrack.deps()
                b: int = zntrack.deps()

                result: int = zntrack.outs()

                def run(self) -> None:
                    self.result = self.a * self.b

We will now define a workflow connecting multiple :term:`Node` instances.
As you can see, ZnTrack allows you to connect the Nodes directly through their attributes.
It is important to consider the ``main.py`` file purely as a workflow configuration file.
A great explanation for this is given in the `Apache Airflow documentation <https://airflow.apache.org/docs/apache-airflow/stable/tutorial/fundamentals.html#it-s-a-dag-definition-file>`_.


.. note::

    In addition to the predefined fields, here ``a``, ``b`` and ``result``, it is also possible to pass the full :term:`Node` instance as an argument.
    For on-the-fly computations it is further possible to define ``@property`` methods that are not stored in the :term:`Node` state and pass them between :term:`Node` instances.
    The ``@property`` can also be used to define custom file readers.

.. dropdown:: The project context manager

    The workflow is defined within the context manager of the :term:`Project`.
    Instead of passing the actual argument, a :term:`ZnFlow` connection is created between the :term:`Node` instances.
    Besides that, a :term:`Node` can also be used like a regular Python object outside of the context manager.

.. code-block:: python

    import zntrack

    from src import Add, Multiply

    project = zntrack.Project()

    with project:
        add1 = Add(a=1, b=2)
        add2 = Add(a=3, b=4)
        add3 = Multiply(a=add1.result, b=add2.result)

    project.build()

Calling ``project.build()`` will create all configuration files and prepare the project to be executed.

.. dropdown:: ZnTrack configuration files
    :open:

    A ZnTrack project typically consists of three configuration files:

    - ``params.yaml``: Parameters defined in the ``main.py`` file are stored here in per :term:`node name` keys.
    - ``dvc.yaml``: The :term:`DVC` workflow is defined in this file. For more information see `DVC documentation <https://dvc.org/doc/user-guide/project-structure/dvcyaml-files#dvcyaml>`_.
    - ``zntrack.json``: Additional information that is used by ZnTrack to manage the workflow.

    You should not modify the ``dvc.yaml`` and ``zntrack.json`` files manually.
    It is possible to modify the ``params.yaml`` file, but recommended to change the parameters within the ``main.py`` instead, to ensure one source of truth.

To execute the workflow, we make use of the ``dvc`` command line tool.

.. code-block:: bash

    dvc repro

.. tip::

    Instead of calling ``dvc repro`` you can also write ``project.repro()`` instead of ``project.build()``.


Groups
------

To organize the workflow, it is possible to group :term:`Node` instances.
Groups are purely organizational and do not affect the workflow execution.

.. note::

    Each :term:`Node` is given a unique name.
    The name typically consists of the class name followed by a counter.
    If a :term:`Node` is grouped, the group name is prefixed to the :term:`Node` name.
    You can get a list of all :term:`Node` names using the CLI command ``zntrack list``.
    If you want to use a custom name, you can pass the ``name`` argument to the :term:`Node` constructor like so

    .. code-block:: python

        add1 = Add(a=1, b=2, name="custom_name")



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
