Atomistic Simulation
====================


Original code
-------------

.. dropdown:: Dependencies
    
    For this example you will need:

    - https://github.com/ACEsuit/mace
    - https://github.com/m3g/packmol
    - https://github.com/zincware/rdkit2ase


.. literalinclude:: ./pack_box/original.py
    :language: Python


Converted Workflow with ZnTrack
--------------------------------


To make this workflow reproducible, we convert it into a **directed graph
structure** where each step is represented as a **Node**. Nodes define their
inputs, outputs, and the computational logic to execute. Here's the graph
structure for our example:

.. mermaid::

    flowchart LR

    Smiles2Conformers --> Pack --> StructureOptimization
    MACE_MP --> StructureOptimization


.. literalinclude:: ./pack_box/src/__init__.py
    :language: Python


.. literalinclude:: ./pack_box/main.py
    :language: Python

