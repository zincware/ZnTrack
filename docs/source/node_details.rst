More about Nodes
----------------
This section describes some special cases for :term:`Node` definitions.

On and Off Graph Nodes
======================

The :term:`Node` instances we have seen so far are all placed onto the graph.
In other words, they are defined within the context of the :term:`Project` and will have a ``run`` method that is executed when the :term:`Project` runs.

.. note::

    Each of these :term:`Node` instances is represented by an individual stage in the :term:`DVC` graph.

In some cases, a :term:`Node` should provide additional methods but will only be used within other :term:`Node` instances.
Such a :term:`Node` is called "off-graph" and can be represented by a Python ``dataclass``.
They are often used to define an interchangeable model, as illustrated in the example on :ref:`example_classifier_comparison`.
Another use case for off-graph :term:`Node` instances is reusing a :term:`Node` from another project.
If you load a :term:`Node` via ``zntrack.from_rev``, you can also use it as an off-graph :term:`Node`.

In other words, off-graph :term:`Node` instances do not produce any output files when the graph is executed.
They are only used as dependencies for on-graph :term:`Node` instances, which are responsible for creating output files.

.. note::

    Just like on-graph :term:`Node` definitions, it must be possible to import the ``dataclass``-derived :term:`Node`.
    Therefore, it is recommended to place them alongside on-graph :term:`Node` definitions, e.g., in the same module.
    If you define them inside ``main.py``, you must ensure that the :term:`Project` is constructed inside a code block
    after ``if __name__ == "__main__":`` to avoid executing the script when importing the :term:`Node`.

.. code-block:: python

    from dataclasses import dataclass
    import zntrack

    @dataclass
    class Shift:
        shift: float

        def compute(self, input: float) -> float:
            return input + self.shift

    @dataclass
    class Scale:
        scale: float

        def compute(self, input: float) -> float:
            return input * self.scale

    class ManipulateNumber(zntrack.Node):
        number: float = zntrack.params()
        method: Shift | Scale = zntrack.deps()

        result: float = zntrack.outs()

        def run(self) -> None:
            self.result = self.method.compute(self.number)

    if __name__ == "__main__":
        project = zntrack.Project()

        # You can define these Nodes anywhere, but
        # to avoid confusion, they should be placed outside the Project context
        shift = Shift(shift=1.0)
        scale = Scale(scale=2.0)

        with project:
            shifted_number = ManipulateNumber(number=1.0, method=shift)
            scaled_number = ManipulateNumber(number=1.0, method=scale)
        project.repro()

Off-graph :term:`Node` instances can be extended with :meth:`zntrack.params_path` and :meth:`zntrack.deps_path` to define parameters and dependencies, which will be connected to the :term:`Node` they are used in.
This can be useful e.g. when defining a method that uses a parameter file or requires a specific file dependency without providing a run method and thus not being a :term:`Node` itself.

.. code-block:: python

    from dataclasses import dataclass
    import yaml
    import zntrack

    @dataclass
    class Calculator:
        config_file: str = zntrack.params_path()
        model_path: str = zntrack.deps_path()

        def get_calculator(self):
            with open(self.config_file, "r") as f:
                config = yaml.safe_load(f)
            return func(model=self.model_path, **config)

.. warning::

    Reading files without using the DVCFileSystem in dataclasses will lead to errors when using ``zntrack.from_rev()`` with a ``rev`` or ``remote`` argument.

Always Changed
==============

In some cases, you may want a :term:`Node` to always run, even if the inputs have not changed.
This can be useful when debugging a new :term:`Node`.
In such cases, you can set ``always_changed=True``.

.. code-block:: python

    import zntrack.examples

    project = zntrack.Project()

    with project:
        node = zntrack.examples.ParamsToOuts(params=42, always_changed=True)

    project.repro()

Node State
==========

Each :term:`Node` provides a ``state`` attribute to access metadata or the `DVCFileSystem <https://dvc.org/doc/api-reference/dvcfilesystem>`_.
The :meth:`zntrack.state.NodeStatus` is ``frozen`` and read-only.

.. autoclass:: zntrack.state.NodeStatus
    :members: use_tmp_path, fs


.. _zntrack_apply:

Custom Run Methods
==================

By default, a :term:`Node` will execute the ``run`` method.
Sometimes, it is useful to define multiple methods for a single :term:`Node` with slightly different behavior.
This can be achieved by using :meth:`zntrack.apply`.

.. autofunction:: zntrack.apply

Entry Points
============

If you are developing a package based on ZnTrack, you can expose your :term:`Node` definitions to other packages.

You can define one or more groups of Nodes and register them using a function like this:

.. code-block:: python

    import zntrack

    def nodes() -> list[zntrack.Node]:
        return [
            mypackage.MyNode1,
            mypackage.MyNode2,
        ]

This function should be registered as an entry point in your ``pyproject.toml``:

.. code-block:: toml

    [project.entry-points."zntrack.nodes"]
    mypackage = "mypackage.nodes:nodes"

Each entry represents a group of Nodes.
If your Nodes are organized into different categories, you can define multiple entry points accordingly.
