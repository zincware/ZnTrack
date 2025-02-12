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
- **Lightweight and Database-Free**: ZnTrack is lightweight and does not require any databases.
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
      y = add(x, 3)
      print(y)
      >>> 6


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
         y = Add(a=x.result, b=3)
      
      project.repro()

      print(y.result)
      >>> 6

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

.. toctree::
   :hidden:
   :maxdepth: 2

   node
   project
   glossary
   
