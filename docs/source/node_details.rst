More about Nodes
----------------

On and Off Graph Nodes
======================

The :term:`Node` we have seen so far are all put onto the graph.
In other words, they are defined within the context of the :term:`Project` and will have a ``run`` method that is executed when the :term:`Project` is run.

.. note::

    Each of these :term:`Node` instances is represented by an indivual stage in the :term:`DVC` graph.

In some cases a :term:`Node` should provide some additional methods but will only be used within other :term:`Node` instances.
Such a :term:`Node` is called "off-graph" and can be represented by a Python ``dataclass``.
They are often used to define a exchangeable model as illustrated in the example on :ref:`example_classifier_comparison`.

.. note::

    Just like the on-graph :term:`Node` defintions it must be possible to import the ``dataclass`` dervied :term:`Node`.
    Therefore, it is recommended to put them next to the on-graph :term:`Node` definitions, e.g. in the same module.
    If you define them inside the ``main.py`` you must make sure to construct the :term:`Project` in a code code-block
    after ``if __name__ == "__main__":`` to avoid running the script when importing the :term:`Node`.

.. code-block:: python

    from dataclasses import dataclass
    import zntrack

    @dataclass
    class Shift:
        shift: float

        def compute(self, input:float) -> float:
            return input + self.shift
    
    @dataclass
    class Scale:
        scale: float

        def compute(self, input:float) -> float:
            return input * self.scale

    class ManipulateNumber(zntrack.Node):
        number: float = zntrack.params()
        method: Shift|Scale = zntrack.deps()

        results: float = zntrack.outs()

        def run(self) -> None:
            self.result = self.method.compute(self.number)

    
    if __name__ == "__main__":
        project = zntrack.Project()

        # you can define these Nodes everywhere, but
        # to avoid confusion they should be put outside the Project context
        shift = Shift(shift=1.0)
        scale = Scale(scale=2.0)

        with project:
            shifted_number = ManipulateNumber(number=1.0, method=shift)
            scaled_number = ManipulateNumber(number=1.0, method=scale)
        project.repro()
