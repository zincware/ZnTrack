.. _example_classifier_comparison:

Scikit-learn classifier comparison
==================================

Original code
-------------

.. dropdown:: Dependencies

    For this example you will need:

    - https://scikit-learn.org/stable/install.html

In this example we will adapt the `classifier comparison example <https://scikit-learn.org/stable/auto_examples/classification/plot_classifier_comparison.html#sphx-glr-auto-examples-classification-plot-classifier-comparison-py>`_ from the scikit-learn documentation to use ZnTrack.

The original code looks like this:

.. dropdown:: Original code
    :open:

    .. literalinclude:: ./classifier_comparison/original.py
        :language: Python


Converted Workflow with ZnTrack
--------------------------------

We can now adapt the scikit-learn example to utilize ZnTrack.
This allows us to store and share the results and reuse the code by a better seperation into individual :term:`Node` for each task.
Further, we can easily optimize parameters and compare different classifiers via tools of the :term:`DVC` infrastructure.
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
