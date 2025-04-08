classifier_comparison.rst

.. _example_classifier_comparison:

Scikit-learn Classifier Comparison
==================================

Original Code
-------------

.. dropdown:: Dependencies

    For this example, you will need:

    - https://scikit-learn.org/stable/install.html

This example adapts the `classifier comparison example <https://scikit-learn.org/stable/auto_examples/classification/plot_classifier_comparison.html#sphx-glr-auto-examples-classification-plot-classifier-comparison-py>`_ from the scikit-learn documentation to use ZnTrack.

The original code looks like this:

.. dropdown:: Original Code
    :open:

    .. literalinclude:: ./classifier_comparison/original.py
        :language: Python

Converted Workflow with ZnTrack
-------------------------------

We adapt the scikit-learn example to utilize ZnTrack.
This allows us to store, share results, and reuse the code by better separating it into individual :term:`Node` instances for each task.
Additionally, we can optimize parameters and compare different classifiers more effectively using :term:`DVC` infrastructure tools.

Here's the graph structure for a single dataset and multiple classifiers:

.. mermaid::

    flowchart TD

    Dataset --> TrainTestSplit
    subgraph Classifier
        KNeighborsClassifier
        SVC
        GaussianProcessClassifier
        DecisionTreeClassifier
        RandomForestClassifier
        a["..."]
    end
    TrainTestSplit --> KNeighborsClassifier --> Compare
    TrainTestSplit --> SVC --> Compare
    TrainTestSplit --> GaussianProcessClassifier --> Compare
    TrainTestSplit --> DecisionTreeClassifier --> Compare
    TrainTestSplit --> RandomForestClassifier --> Compare
    TrainTestSplit --> a["..."] --> Compare

.. dropdown:: ZnTrack Nodes
    :open:

    .. literalinclude:: ./classifier_comparison/src/__init__.py
        :language: Python

.. dropdown:: ZnTrack Workflow
    :open:

    .. literalinclude:: ./classifier_comparison/main.py
        :language: Python

Generated configuration files
-----------------------------

.. dropdown:: dvc.yaml File

    .. literalinclude:: ./classifier_comparison/dvc.yaml
        :language: YAML

.. dropdown:: params.yaml File

    .. literalinclude:: ./classifier_comparison/params.yaml
        :language: YAML

.. dropdown:: zntrack.json File

    .. literalinclude:: ./classifier_comparison/zntrack.json
        :language: JSON
