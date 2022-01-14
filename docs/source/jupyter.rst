Jupyter Support
===============

ZnTrack provides experimental Jupyter notebook support for DVC.
This allows for the use of DVC without writing custom python files for every stage.

To provide ZnTrack functionality within Jupyter Notebooks, we convert the
notebook into a :code:`*.py` file and then extract the class definitions.
For every ZnTrack Node a file in :code:`src` is generated.
These files will be used by DVC to run the stage.

Because copying the content to a new file can cause major issues and there
are only limited testing possibilities, this feature is considered highly experimental.
If you want to use it, you can follow the Example Notebooks.

In general one may write:

.. code-block:: python

    from zntrack import Node, config, zn,

    config.nb_name="JupyterZnTrack.ipynb"

    class Stage(Node):
        output = zn.outs()
        def run(self):
            """Actual computation"""
            self.output = "lorem ipsum"

Here :code:`nb_name` has to match the name of the notebook, because we can not easily identify this name during runtime.
Then you can run :code:`stage = Stage.load()` as usual.