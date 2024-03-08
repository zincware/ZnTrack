.. _userdoc-project:

Project
=======
You can run ZnTrack nodes in three different ways.
Let's assume the following two nodes:

..  code-block:: python

    import zntrack

    class AddOne(zntrack.Node):
        parameter: int = zntrack.params()
        outputs: int = zntrack.outputs()

        def run(self):
            self.outputs = self.parameter + 1

    class SubtractOne(zntrack.Node):
        parameter: int = zntrack.deps()
        outputs: int = zntrack.outputs()

        def run(self):
            self.outputs = self.parameter - 1

Direct Use
----------
ZnTrack Nodes are designed to be used as regular Python classes.
This allows for easy debugging and testing.
Typically, you would use :ref:`target to eager graph` or :ref:`target to dvc graph` for production.

..  code-block:: python

    node1 = AddOne(parameter=1)
    node1.run()

    node2 = SubtractOne(parameter=node1.outputs)
    node2.run()

    assert node1.outputs == 2
    assert node2.outputs == 1

.. _target to eager graph:

Eager graph
-----------
You can use ZnTrack without DVC.
This closely resembles the `ZnFlow <https://github.com/zincware/znflow>`_ package.
ZnTrack is built on top of it.
The general API would look as follows:

..  code-block:: python

    with zntrack.Project() as project:
        node1 = AddOne(parameter=1)
        node2 = SubtractOne(parameter=node1.outputs)

    project.run(eager=True)
    assert node1.outputs == 2
    assert node2.outputs == 1

.. _target to dvc graph:

DVC
---
The main purpose of ZnTrack is to use it with DVC.
If you use ``project.run()`` it will serialize the Nodes inside the project and run them with DVC.
You can use ``project.run(repro=False)`` to only build the graph and execute it later.

..  code-block:: python

    with zntrack.Project() as project:
        node1 = AddOne(parameter=1)
        node2 = SubtractOne(parameter=node1.outputs)

    project.run()

    node1.load()
    node2.load()

    assert node1.outputs == 2
    assert node2.outputs == 1
