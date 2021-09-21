Jupyter Support
===============

PyTrack provides experimental Jupyter notebook support for DVC.
This allows for the use of DVC without writing custom packages.

To provide PyTrack functionality within Jupyter Notebooks, we convert the
notebook into a *.py file and then extract the class definitions.
For every PyTrack class defined a file in :code:`src` is generated.
These files will be used by DVC to run the stage.

Because copying the content to a new file can cause major issues and there
are only a limited testing possibilities, this feature is considered highly experimental.
If you want to use it, you can follow the Example Notebooks.

In general one may write:

.. code-block:: python

    from pytrack import PyTrack, parameter, result, DVCParams,

    nb_name="JupyterPyTrack.ipynb"

    @PyTrack(nb_name=nb_name)
    class Stage:
        def __init__(self):
            """Class constructor

            Definition of parameters and results
            """
            self.dvc = DVCParams(outs=['calculation.txt'])

            self.n_1 = parameter(int)  # seems optional now
            self.n_2 = parameter()

            self.sum = result()
            self.dif = result()

        def __call__(self, n_1, n_2):
            """User input

            Parameters
            ----------
            n_1: First number
            n_2: Second number
            """
            self.n_1 = n_1
            self.n_2 = n_2

        def run(self):
            """Actual computation"""
            self.sum = self.n_1 + self.n_2
            self.dif = self.n_1 - self.n_2

            self.dvc.outs[0].write_text(f"{self.n_1} + {self.n_2} = {self.sum}")

Here :code:`nb_name` has to match the name of the notebook, because we can not
easily identify this name during runtime.
Then you can run :code:`stage = Stage(id_=0)` as usual.