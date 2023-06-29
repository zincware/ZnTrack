Connecting Nodes
================

..
    **# TODO: Connect function and class based nodes**

The strength of the ZnTrack package is within connecting nodes.
This is easily done by passing one Node as an argument to another one.

Let us assume two Nodes ``GenerateData`` and ``ProcessData``.
We can connect these Nodes as follows:

.. code-block:: python

    with zntrack.Project() as project:
        generate_data = GenerateData(**kwargs)
        process_data = ProcessData(data=load_data)
    project.run()

Now, the ``process_data.data`` attribute will be the loaded instance of ``GenerateData``, when running ``dvc repro``.
The following connection has been established:

.. image:: https://mermaid.ink/img/pako:eNptzjELwjAQBeC_Ut7cDnXM4FRwFXTzOhzJ1RaaRNILIqX_3VRcBN908D64t8JGJzAY5vi0Iyetrh2F6ptQyvZGOEmQxCodKxP6X3Ao4JyilWX527dNc_w41PCSPE-uPFx3RNBRvBBMOZ0MnGclUNgK5azx8goWRlOWGvnh9gUT3xN7mIHnRbY3T449Ig?type=png
    :alt: mermaid diagram

In some cases it is useful to connect Node attributes instead of Nodes.
This can be achieved in the same way.

.. code-block:: python

    with zntrack.Project() as project:
        generate_data = GenerateData(**kwargs)
        process_data = ProcessData(data=generate_data.data)
    project.run()

.. tip::
    You can also pass ``list`` or ``dict`` of Nodes or Node attributes to other Nodes.
    This allows to easily build sophisticated pipelines with ZnTrack and DVC.
