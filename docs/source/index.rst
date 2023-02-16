.. ZnTrack documentation master file, created by
   sphinx-quickstart on Mon Feb  6 15:28:26 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

ZnTrack's documentation!
========================

.. image:: _static/logo_ZnTrack.png
   :alt: ZnTrack logo
   :target: https://github.com/zincware/ZnTrack

.. raw:: html

   <iframe src="https://ghbtns.com/github-btn.html?user=zincware&repo=zntrack&type=star&count=true&size=large" frameborder="0" scrolling="0" width="130" height="30" title="GitHub"></iframe>
   <iframe src="https://ghbtns.com/github-btn.html?user=zincware&repo=zntrack&type=fork&count=true&size=large" frameborder="0" scrolling="0" width="130" height="30" title="GitHub"></iframe>

ZnTrack is `zincware's <https://github.com/zincware>`_ first developer package and in fact, the first released on PyPi, so we are glad you are here. ZnTrack is built to help you write code that can easily be shared and reproduced.

- :ref:`userdoc-get-started`
- :ref:`userdoc-examples`
- :ref:`userdoc-theory`
- :ref:`userdoc-api`


Example
=======

Here are two examples of how ZnTrack Nodes can look like.
ZnTrack supports function and class based Nodes, as well as the combination of both.
For more information, refer to the :ref:`userdoc-get-started` section.

Class based Node
----------------
.. code-block:: python

   from zntrack import Node, zn

   class AddNumbers(Node):
      number1 = zn.params()
      number2 = zn.params()

      result = zn.outs()

      def run(self):
         self.result = self.number1 + self.number2

   AddNumbers(number1=10, number2=20).write_graph()


Function based Node
-------------------
 .. code-block:: python

   from zntrack import nodify, NodeConfig

   @nodify(outs="number.txt", params={"number1": 10, "number2": 20})
   def add_numbers(cfg: NodeConfig):
      with open(cfg.outs) as file:
            file.write(str(cfg.params.number1 + cfg.params.number2))

   add_numbers()


.. toctree::
   :hidden:

   _get-started/index
   _examples/index
   _theory/index
   _api/index