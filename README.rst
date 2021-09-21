|build| |docs| |license| |code style|

PyTrack
-------
A Python package to use DVC for parameter and data control

For more information on DVC visit their `homepage <https://dvc.org/doc>`_.

Example
========
PyTrack allows you to convert most Python classes into a DVC stage, including parameters, dependencies and all DVC output types.

.. code-block:: py

    from pytrack import PyTrack, DVC


    @PyTrack()
    class Linear:
        def __init__(self):
            """Define all DVC parameter, dependencies and outputs"""
            self.values_file = DVC.deps()
            self.a1 = DVC.params()
            self.b = DVC.params()
            self.out = DVC.result()

        def __call__(self, a1, b, values_file):
            """
            Parameters
            ----------
            a1: float
                Any a1 for calculating a1 * x + b
            b: float
                Any b for calculating a1 * x + b
            values_file: str
                Path to a comma seperated file of values for x
            """
            self.values_file = values_file
            self.a1 = a1
            self.b = b

        def run(self):
            """Command that is run by DVC"""
            values = [float(x) for x in self.values_file.read_text().split(",")]
            self.out = [self.a1 * x + self.b for x in values]

This stage can be used via

.. code-block:: py

    linear = Linear()
    linear(3, 7, "values.csv")

which builds the DVC stage and can be used e.g., through :code:`dvc repro`.
The results can then be accessed easily via :code:`Linear(id_=0).out`.


Installation
============

Simply run:

.. code-block:: bash

   pip install py-track

Or you can install from source with:

.. code-block:: bash

   git clone https://github.com/zincware/py-track.git
   cd py-track
   pip3 install .

.. badges

.. |build| image:: https://github.com/zincware/py-track/actions/workflows/pytest.yaml/badge.svg
    :alt: Build tests passing
    :target: https://github.com/zincware/py-test/blob/readme_badges/

.. |docs| image:: https://readthedocs.org/projects/py-track/badge/?version=latest&style=flat
    :alt: Build tests passing
    :target: https://py-track.readthedocs.io/en/latest/

.. |license| image:: https://img.shields.io/badge/License-EPL-purple.svg?style=flat
    :alt: Project license
    :target: https://www.eclipse.org/legal/eplfaq.php

.. |code style| image:: https://img.shields.io/badge/code%20style-black-black
    :alt: Code style: black
    :target: https://github.com/psf/black/
