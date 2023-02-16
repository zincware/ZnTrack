.. _userdoc-get-started-api_classes:

Node Class: The Backbone of ZnTrack
===================================

The ``zntrack.Node`` class is at the core of ZnTrack's functionality.
It serves as the base class for class-based Nodes on the Graph.
Compared to the function-based approach, the class-based approach has several advantages:

- The state of the Node is stored as class attributes, providing greater flexibility.
- Python classes enable more complex logic to be defined.
- The class can be easily reused in other Nodes.
- The class state can be serialized more easily.
- Parameters, inputs, and outputs are handled as class attributes, simplifying the creation of new Nodes.

To define a custom Node, simply inherit from the Node class. Parameters and outputs can be defined in two ways. The ``from zntrack import zn`` module enables seamless integration with your existing workflows, allowing Python objects to be automatically serialized.


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