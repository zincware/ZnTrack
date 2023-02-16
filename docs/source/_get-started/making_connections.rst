Connecting Nodes
================

..
    **# TODO: Connect function and class based nodes**

The strength of the ZnTrack package is within connecting nodes.
This is easily done by passing one Node as an argument to another one.

Let us assume two Nodes ``GenerateData`` and ``ProcessData``.
We can connect these Nodes as follows:

.. code-block:: python

    generate_data = GenerateData(**kwargs)
    process_data = ProcessData(data=load_data)

Now, the ``process_data.data`` attribute will be the loaded instance of ``GenerateData``, when running ``dvc repro``.
The following connection has been established:

.. image:: https://mermaid.ink/img/pako:eNptzjELwjAQBeC_Ut7cDnXM4FRwFXTzOhzJ1RaaRNILIqX_3VRcBN908D64t8JGJzAY5vi0Iyetrh2F6ptQyvZGOEmQxCodKxP6X3Ao4JyilWX527dNc_w41PCSPE-uPFx3RNBRvBBMOZ0MnGclUNgK5azx8goWRlOWGvnh9gUT3xN7mIHnRbY3T449Ig?type=png
    :alt: mermaid diagram

In some cases it is useful to connect Node attributes instead of Nodes.
In the above example the Node ``ProcessData`` has to know the correct attributes of ``GenerateData`` to e.g. access the ``data``.
Therefore, one can also connect attributes of Nodes.
This is done by appending ``@`` and the attribute name to the Node.
With this, any attribute of any Node can be connected.

.. code-block:: python

    generate_data = GenerateData(**kwargs)
    process_data = ProcessData(data=generate_data @ "data")

.. tip::
    In a Future release of ZnTrack it will be possible to connect Nodes directly inside a Context Manager.
    The current API will still remain but it can be worth looking for updates of the ZnTrack package.
    Check out `ZnFlow <https://github.com/zincware/znflow>`_ for a preview and further information.

    .. code-block:: python

        with zntrack.DiGraph() as graph:
            generate_data = GenerateData(**kwargs)
            process_data = ProcessData(data=generate_data.data)