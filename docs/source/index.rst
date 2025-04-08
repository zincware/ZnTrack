ZnTrack Documentation
=====================

ZnTrack (``zɪŋk træk``) is a lightweight and easy-to-use Python package for converting existing Python code into reproducible workflows.
By structuring your code as a directed graph with well-defined inputs and outputs, ZnTrack ensures reproducibility, scalability, and ease of collaboration.


Key Features
------------

- **Reproducible Workflows**: Convert Python scripts into reproducible workflows with minimal effort.
- **Parameter, Output, and Metric Tracking**: Easily track parameters, outputs, and metrics in your Python code.
- **Shareable and Collaborative**: Work together with your team using Git. Share your workflows, reuse components in other projects, or package them as Python modules.
- **DVC Integration**: ZnTrack is built on top of :term:`DVC` for version control and experiment management, seamlessly integrating into the :term:`DVC` ecosystem.

Installation
------------
You can install ZnTrack via pip:

.. code-block:: bash

   pip install zntrack


Example
-------
Let’s convert a simple Python script into a reproducible workflow using ZnTrack.

.. code-block:: python

   def add(a: int, b: int) -> int:
       return a + b

   if __name__ == "__main__":
      x = add(1, 2)
      print(x)
      >>> 3

We will now transform this function into a :term:`Node` and build a directed workflow graph using ZnTrack.

.. note::

   A ZnTrack :term:`Project` always requires a :term:`GIT` and :term:`DVC` repository.
   Initialize a new project by running the following commands:

   .. code-block:: bash

      mkdir my_project
      cd my_project
      git init
      dvc init
      touch main.py # Add the code below to main.py

.. code-block:: python

   import zntrack

   class Add(zntrack.Node):
      a: int = zntrack.params()
      b: int = zntrack.params()
      result: int = zntrack.outs()

      def run(self) -> None:
         self.result = self.a + self.b

   if __name__ == "__main__":
      project = zntrack.Project()

      with project:
         x = Add(a=1, b=2)

      project.repro()

      print(x.result)
      >>> 3

ZnTrack uses Python classes instead of functions to define a :term:`Node`.
This approach differs from most other workflow management tools and is motivated by the need to store all inputs and outputs of a Node, making each :term:`Node` stateful.

Once a :term:`Node` has been executed, you can access its results at any time.
Each :term:`Node` is uniquely identified by its :term:`node name` and the :term:`git` :term:`commit hash`.

.. code-block:: python

   import zntrack

   x = zntrack.from_rev(name="Add", rev="HEAD", remote="https://github.com/user/repo")
   print(x.result)
   >>> 3

.. note::

   You can omit the ``remote`` and ``rev`` parameters to load a :term:`Node` from the current repository and commit.


.. dropdown:: Projects using ZnTrack
   :open:

   .. card:: MLIPX

      ``mlipx`` is a Python library designed for evaluating machine-learned interatomic potentials. It offers a growing set of evaluation methods alongside powerful visualization and comparison tools.
      +++
      https://github.com/basf/mlipx

   .. card:: IPSuite

      IPSuite provides tools for generating machine-learned interatomic potentials.
      +++
      https://github.com/zincware/ipsuite

   .. card:: Apax

      Apax is a high-performance, extendable package for training and inference with atomistic neural networks.
      +++
      https://github.com/apax-hub/apax

   .. card:: ZnDraw

      ZnDraw is a powerful tool for visualizing and interacting with atomistic trajectories.
      +++
      https://github.com/zincware/zndraw

   .. card:: Paraffin

      A DVC graph executor and progress visualization tool.

      .. tip::

         Paraffin can be used with or without ZnTrack and provides powerful tools for distributed execution of :term:`DVC` graphs, along with a graphical user interface for monitoring progress.

      +++
      https://github.com/zincware/paraffin


.. toctree::
   :hidden:
   :maxdepth: 2

   node
   project
   fields
   node_details
   examples/examples
   glossary
