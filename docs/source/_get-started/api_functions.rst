.. _userdoc-get-started-api_functions:

Function Decorator: @nodify
===========================

@nodify
-------

ZnTrack allows us to convert a Python function into a Node on the graph.

..  code-block:: python

    from zntrack import nodify, NodeConfig
    import pathlib


    @nodify(outs=pathlib.Path("outs.txt"), params={"text": "Lorem Ipsum"})
    def write_text(cfg: NodeConfig) -> None:
        cfg.outs.write_text(cfg.params.text)

We convert the function ``write_text`` into a Node by using the decorator ``@nodify``.
We specify two arguments:

- ``outs``: The output of the Node. This can be a single file, a list of files or directories.
- ``params``: The parameters of the Node. A dictionary of values used as parameters.

The ``write_text`` function receives these arguments as a ``NodeConfig`` object.
To put the Node on the graph, we need to run it inside the ``zntrack.Project``.


..  caution::
    The ``write_text`` function can not have any other arguments or any return value.
    All computations have to be saved to disk. This is a DVC requirement, to ensure reproducibility.

Gather results
--------------
To access the results, we need to run the graph using ``project.run()`` or ``dvc repro``.
This will run the Node and save the results to disk.
The file ``outs.txt`` is created with the content ``Lorem Ipsum``.
At this stage, running the graph again using ``dvc repro`` won't have an affect.
This is because the Node does not have changes to its inputs or parameters.
If we edit ``params.yaml`` and change the text to ``Hello World``, running ``dvc repro`` again will update the output file.

.. tip::

    If we change the ``params.yaml`` file contents back to ``Lorem Ipsum``, calling ``dvc repro`` again will load the results from the run cache. See `DVC run cache <https://dvc.org/doc/user-guide/project-structure/internal-files#run-cache>`_ for more information.



Explanation
-----------

Running the Node above from ``main.py`` will create the following files for us.
The ``params.yaml`` file contains the parameter we passed to the ``write_text`` function.
It is designed to be edited by the user to run the workflow with different parameters

The ``dvc.yaml`` file contains the definition of the computational graph.
It is automatically generated and should not be edited by the user directly.
To update the graph, update ``main.py`` and run it again.

The ``zntrack.json`` file contains some additional information about the Nodes.
It is automatically generated and should not be edited by the user directly.


.. tip::
    ZnTrack Nodes can easily be combined with standard DVC stages.
    Typically, these stages are created by ``dvc stage add`` but can also be created manually.
    ZnTrack will only change entries related to the Nodes that are called in ``main.py``.
    If changes are made to ZnTrack nodes defined in ``dvc.yaml`` make sure, to check ``zntrack.json`` and ``main.py`` as well.


..  code-block:: yaml
    :caption: params.yaml

    write_text:
        text: Lorem Ipsum


..  code-block:: yaml
    :caption: dvc.yaml

    stages:
      write_text:
        cmd: zntrack run main.write_text
        params:
        - write_text
        outs:
        - outs.txt

..  code-block:: json
    :caption: zntrack.json

    {
        "write_text": {
            "outs": {
                "_type": "pathlib.Path",
                "value": "outs.txt"
            },
            "outs_no_cache": null,
            "outs_persist": null,
            "outs_persist_no_cache": null,
            "metrics": null,
            "metrics_no_cache": null,
            "deps": null,
            "plots": null,
            "plots_no_cache": null
        }
    }
