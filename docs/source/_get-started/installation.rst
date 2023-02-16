.. _userdoc-installation:

Installation
============

The ZnTrack package is available on PyPI and can be installed using

..  code-block:: bash

    pip install zntrack

Developer Installation
----------------------

ZnTrack is developed using `Poetry <https://python-poetry.org/>`_.
To install the package in development mode, clone the repository and use ``poetry install``.
Instead of using the poetry environment you can also use ``conda create -n zntrack python`` and ``conda activate zntrack`` before installing the package.

..  code-block:: bash

    git clone https://github.com/zincware/ZnTrack.git
    cd ZnTrack
    poetry install
