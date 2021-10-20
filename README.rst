|build| |docs| |license| |code style|

Node
-------
A Python package to use DVC for parameter and data control

For more information on DVC visit their `homepage <https://dvc.org/doc>`_.

Example
========
Node allows you to convert most Python classes into a DVC stage, including
parameters, dependencies and all DVC output types.

.. code-block:: py

    from pytrack import Node, DVC
    from random import randrange


    @Node()
    class HelloWorld:
        """Define a Node Stage"""
        # parameter to be tracked
        max_number = DVC.params()   
        # parameter to store as output
        random_number = DVC.result()  

        def __call__(self, max_number):
            """Pass tracked arguments"""
            self.max_number = max_number

        def run(self):
            """Command to be run by DVC"""
            self.random_number = randrange(self.max_number)

This stage can be used via

.. code-block:: py

    hello_world = HelloWorld()
    hello_world(max_number=512)

which builds the DVC stage and can be used e.g., through :code:`dvc repro`.
The results can then be accessed easily via :code:`HelloWorld(load=True).random_number`.


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
    :target: https://www.eclipse.org/legal/epl-2.0/faq.php

.. |code style| image:: https://img.shields.io/badge/code%20style-black-black
    :alt: Code style: black
    :target: https://github.com/psf/black/
