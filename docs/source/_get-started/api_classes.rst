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

To define a custom Node, simply inherit from the Node class. Parameters and outputs can be defined in two ways.
The ``zntrack.<field>`` enables seamless integration with your existing workflows, allowing Python objects to be automatically serialized.
Alternatively, you can use the ``zntrack.params_path()`` and ``zntrack.outs_path()`` to define the paths to the respective files.

..  code-block:: python

    import zntrack

    class SumValues(zntrack.Node):
        """Node to compute the sum of two parameters."""
        a = zntrack.params()
        b = zntrack.params()

        result = zntrack.outs()

        def run(self):
            """Compute the sum of two parameters."""
            self.result = self.a + self.b

    if __name__ == "__main__":
        with zntrack.Project() as project:
            node = SumValues(a=1, b=2)
        project.run(repro=False)

We define our parameter using ``zntrack.params()`` and define the respective output using ``zntrack.outs()``.

Gather results
--------------

Using ``project.run(repro=False)`` will add the Node as a stage to the DVC Graph.
To access the results, we need to run the first graph.


..  code-block:: bash

    dvc repro

We can now access the results by loading the Node and accessing the respective attributes.
It is not only possible to access the results, but also the parameters and inputs.

..  code-block:: python

    node.load()
    print(node.result)  # will print 3
    print(node.a)  # will print 1

If you don't have access to the ``node`` object, you can also load the Node based on it's name:

..  code-block:: python

    node = SumValues.from_rev(name="SumValues")

Explanation
-----------

The same files as in the previous ``@nodify`` example are created.
The main difference is the ``outs`` of our Node ``SumValues``.
Using the `zntrack.outs` will store results in the Node Working Directory (``nwd``),
It is typically set as ``nodes/<nodename>``.
The ``outs.json`` file is used, when calling ``node.load()`` to gather the results.


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
