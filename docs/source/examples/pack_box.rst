Atomistic Simulation
====================

Original Code
-------------

.. dropdown:: Dependencies

    For this example, you will need:

    - https://github.com/ACEsuit/mace
    - https://github.com/m3g/packmol
    - https://github.com/zincware/rdkit2ase

.. literalinclude:: ./pack_box/original.py
    :language: Python

Converted Workflow with ZnTrack
-------------------------------

To ensure reproducibility, we convert this workflow into a **directed graph structure**, where each step is represented as a **Node**. Nodes define their inputs, outputs, and the computational logic to execute.

Here's the graph structure for our example:

.. mermaid::

    flowchart LR

    Smiles2Conformers --> Pack --> StructureOptimization
    MACE_MP --> StructureOptimization

.. literalinclude:: ./pack_box/src/__init__.py
    :language: Python

.. literalinclude:: ./pack_box/main.py
    :language: Python

Generated configuration files
-----------------------------

.. dropdown:: dvc.yaml File

    .. literalinclude:: ./pack_box/dvc.yaml
        :language: YAML

.. dropdown:: params.yaml File

    .. literalinclude:: ./pack_box/params.yaml
        :language: YAML

.. dropdown:: zntrack.json File

    .. literalinclude:: ./pack_box/zntrack.json
        :language: JSON
