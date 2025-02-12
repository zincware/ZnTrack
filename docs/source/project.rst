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

We will now define a workflow connecting multiple ``Add`` :term:`Node` instances.

.. code-block:: python

    import zntrack

    from src import Add

    project = zntrack.Project()

    with project:
        add1 = Add(a=1, b=2)
        add2 = Add(a=3, b=4)
        add3 = Add(a=add1.result, b=add2.result)

    project.build()
