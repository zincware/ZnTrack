.. _userdoc-get-started-api_classes:

Base Class: Node
================

Most functionality in ZnTrack is built into the ``zntrack.Node`` class.
It is the base class for class-based Nodes on the Graph.
There are several advantage over the function based approach:

- The state of the Node is stored as class attributes.
- Python classes allow for more complex logic.
- The class can easily be reused in other Nodes.
- The class state can be serialized more easily.
- Parameters, inputs and outputs are handled as class attributes and not via ``NodeConfig``.

To define a custom Node it has to inherit from the Node class.
One can define parameters and outputs in two different ways.
The ``from zntrack import zn`` module allows you to automatically serialize Python objects.
This way almost seamlessly integrates in your existing workflows.


..  code-block:: python

    from zntrack import Node, zn

    class SumValues(Node):
        """Node to compute the sum of two parameters."""
        a = zn.params()
        b = zn.params()

        result = zn.outs()

        def run(self):
            """Compute the sum of two parameters."""
            self.result = self.a + self.b

    if __name__ == "__main__":
        SumValues(a=1, b=2).write_graph()

We define our parameter using ``zn.params()`` and define the respective output using ``zn.outs()``.

Gather results
--------------

Using ``<Node>.write_graph()`` will add the Node as a stage to the DVC Graph.
To access the results, we need to run the first graph.


..  code-block:: bash

    dvc repro

We can now access the results by loading the Node and accessing the respective attributes.
It is not only possible to access the results, but also the parameters and inputs.

..  code-block:: python

    sum_values = SumValues.load()
    print(sum_values.result)  # will print 3
    print(sum_values.a)  # will print 1

Explanation
-----------

The same files as in the previous ``@nodify`` example are created.
The main difference is the ``outs`` of our Node ``SumValues``.
Using the `zntrack.zn` module will store results in the Node Working Directory (``nwd``),
It is typically set as ``nodes/<nodename>``.
The ``outs.json`` file is used, when calling ``SumValues.load()`` to gather the results.


..  code-block:: yaml
    :caption: params.yaml

    SumValues:
        a: 1
        b: 2


..  code-block:: yaml
    :caption: dvc.yaml

    stages:
      SumValues:
        cmd: zntrack run main.SumValues --name=SumValues
        params:
        - SumValues
        outs:
        - nodes/SumValues/outs.json

..  code-block:: json
    :caption: zntrack.json

    {}