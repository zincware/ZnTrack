Glossary
========

.. glossary::

    DVC
        Data Version Control. A tool for versioning datasets, machine learning models, and other large files.
        DVC integrates with Git to manage and track changes in data pipelines.
        For more information, see `DVC <https://dvc.org/>`_.

    Node
        The core component of ZnTrack defining a unit of computation to be used in a workflow.
        A Node encapsulates inputs, outputs, and the logic to transform inputs into outputs.
        For more information, see :ref:`node`.

    Node name
        A unique identifier for a Node within a ZnTrack project.
        The name is used to reference the Node in workflows and to organize its outputs.

    GIT
        A distributed version control system used to track changes in source code and collaborate on software development.
        ZnTrack integrates with Git to version workflows and their outputs.

    Commit hash
        A unique identifier for a specific commit in a Git repository.
        In ZnTrack, the commit hash is often used to version and reference the state of a workflow or its outputs.

    NWD
        The Node Working Directory.
        A directory specific to a Node where its outputs are stored.
        The NWD ensures that each Node's files are isolated and organized.

    Project
        A ZnTrack project is a collection of Nodes combined into a directed acyclic workflow graph which defines the computational pipeline.
        A project is typically versioned using Git and DVC.

    ZnFlow
        The ZnFlow workflow manager. For more information see `ZnFlow <https://github.com/zincware/znflow>`_.
