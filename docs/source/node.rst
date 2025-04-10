.. _node:

Node
====

A :term:`Node` is the core component of ZnTrack, defining a unit of computation used in a workflow.
It encapsulates a self-contained piece of logic that can be executed independently or as part of a larger pipeline.

.. note::

    The :term:`Node` is built on top of Python's `dataclasses <https://docs.python.org/3/library/dataclasses.html>`_,
    leveraging their simplicity and power to define structured, reusable components.

A :term:`Node` consists of three key parts:

Inputs
------
Every parameter or dependency required to run the :term:`Node`.
Inputs define the data or configuration that the :term:`Node` needs to perform its computation.
Possible inputs include:

* :meth:`zntrack.params` for JSON-serializable data, e.g., ``{"loss": "mse", "epochs": 10}``.
* :meth:`zntrack.params_path` for parameter files. See `parameter dependencies <https://dvc.org/doc/user-guide/pipelines/defining-pipelines#parameter-dependencies>`_ for more information.
* :meth:`zntrack.deps` for dependencies from another :term:`Node`. More details are provided in the :ref:`Project` section.
* :meth:`zntrack.deps_path` for file dependencies. See `simple dependencies <https://dvc.org/doc/user-guide/pipelines/defining-pipelines#simple-dependencies>`_ for more information.

Outputs
-------
Every result produced by the :term:`Node`.
Outputs are the data or artifacts generated after the :term:`Node` has executed its logic.
Possible outputs include:

* :meth:`zntrack.outs` for any output data. This uses JSON and `pickle <https://docs.python.org/3/library/pickle.html>`_ to serialize data.
* :meth:`zntrack.outs_path` to define an output file path.
* :meth:`zntrack.metrics` for metrics stored as ``dict[str, int|float]``.
* :meth:`zntrack.metrics_path` for file paths to store `metrics <https://dvc.org/doc/command-reference/metrics>`_.
* :meth:`zntrack.plots` for plots as pandas DataFrames.
* :meth:`zntrack.plots_path` for file paths to store `plots <https://dvc.org/doc/user-guide/experiment-management/visualizing-plots>`_.

Run
---
The function executed when the :term:`Node` is run.
This is where the core computation or logic of the :term:`Node` is defined.

It is also possible to define multiple run methods for a single :term:`Node`, enabling flexible execution strategies depending on the context.
For more details, see :ref:`zntrack_apply`.

Example
-------
ZnTrack integrates features that simplify file writing and reading.
The file paths for fields without the ``_file`` suffix are automatically handled by ZnTrack.
The following example demonstrates how to define a simple :term:`Node` that adds two numbers.

.. code-block:: python

    import zntrack

    class Add(zntrack.Node):  # Inherit from zntrack.Node
        # Define parameters similar to dataclass.Field
        a: int = zntrack.params()
        b: int = zntrack.params()

        # Define an output
        result: int = zntrack.outs()

        def run(self) -> None:
            # Core computation of the Node
            self.result = self.a + self.b

The :term:`Node` above can also be written in a more explicit manner, manually saving and loading inputs and outputs.

.. tip::

    ZnTrack provides an :term:`nwd` path specific to each :term:`Node` in the workflow.
    It is highly recommended to use this path to store all data generated by the :term:`Node` to avoid file name conflicts.

.. code-block:: python

    from pathlib import Path

    class AddViaFile(zntrack.Node):
        params_file: str = zntrack.params_path()
        results_file: Path = zntrack.outs_path(zntrack.nwd / "results.json")

        def run(self) -> None:
            import json

            with open(self.params_file, "r") as f:
                params = json.load(f)

            result = params[self.name]["a"] + params[self.name]["b"]

            self.results_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.results_file, "w") as f:
                json.dump({"result": result}, f)

Design Patterns
---------------
A :term:`Node` should encapsulate a single, well-defined piece of logic to improve readability and maintainability.
However, since communication between :term:`Node` instances occurs through files, excessive splitting can slow down the workflow due to file I/O overhead.
To optimize performance, related tasks that always run together should be grouped within a single :term:`Node`.
For example, if a task can be efficiently parallelized—such as preprocessing data in batches—it is better to handle the parallelization within a single :term:`Node` rather than splitting it into multiple :term:`Node` instances.
