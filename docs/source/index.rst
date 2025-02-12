ZnTrack Documentation
=====================

ZnTrack (``zɪŋk træk``) is a lightweight and easy-to-use Python package for
converting your existing Python code into reproducible workflows. By structuring
your code as a directed graph with well-defined inputs and outputs, ZnTrack
ensures reproducibility, scalability, and ease of collaboration.


Key Features
------------

- **Reproducible Workflows**: Convert Python scripts into reproducible workflows with minimal effort.
- **Parameter, Output, and Metric Tracking**: Easily track parameters, outputs, and metrics in your Python code.
- **Shareable and Collaborative**: Collaborate with your team by working together through GIT. Share your workflows and use parts in other projects or package them as Python packages.
- **DVC Integration**: ZnTrack is built on top of :term:`DVC` for version control and experiment managment and seamlessly integrates into the :term:`DVC` ecosystem.

Installation
------------
You can install ZnTrack via pip:

.. code-block:: bash

   pip install zntrack


Example
-------
Let us convert a simple Python script into a reproducible workflow using ZnTrack.

.. code-block:: python

   def add(a: int, b: int) -> int:
       return a + b

   if __name__ == "__main__":
      x = add(1, 2)
      print(x)
      >>> 3


We will convert the function into a :term:`Node` and build a directed workflow graph using ZnTrack.

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

As you can see, ZnTrack uses ``class`` instead of functions to define a :term:`Node`.
This is different to almost every other workflow management tool and is motivated by the fact that all inputs and outputs from a Node a stored, thus each :term:`Node` is stateful.
At any point after a :term:`Node` was executed you can access it's results.
Each :term:`Node` is uniquely idenfitied by the :term:`node name` and :term:`git` :term:`commit hash`.

.. code-block:: python

   import zntrack

   x = zntrack.from_rev(name="Add", rev="HEAD", remote="https://github.com/user/repo")
   print(x.result)
   >>> 3

.. note::

   You can ommit the remote and the rev parameter to load a :term:`Node` from the current repository and commit.


.. dropdown:: Projects using ZnTrack
   :open:

   .. card:: MLIPX

      ``mlipx`` is a Python library designed for evaluating machine-learned interatomic potentials (MLIPs). It offers a growing set of evaluation methods alongside powerful visualization and comparison tools.

      https://github.com/basf/mlipx

   .. card:: IPSuite

      IPSuite provides you with tools to generate Machine Learned Interatomic Potentials.

      https://github.com/zincware/ipsuite

   .. card:: Apax

      apax is a high-performance, extendable package for training of and inference with atomistic neural networks.

      https://github.com/apax-hub/apax

   .. card:: ZnDraw

      ZnDraw is a powerful tool for visualizing and interacting with atomistic trajectories.

      https://github.com/zincware/zndraw


.. toctree::
   :hidden:
   :maxdepth: 2

   node
   project
   fields
   glossary
