Installation
============

PyTrack can be most easily installed via pip:

.. code-block:: bash

    pip3 install py-track

If you want to install PyTrack from source you can use

.. code-block:: bash

    git clone https://github.com/zincware/py-track.git
    cd py-track
    pip3 install .

If you are a developer we suggest using

.. code-block:: bash

    pip3 install -e .

If you have cloned the repository you might be interested in building the docs
locally.
This can be done as follows:

.. code-block::bash

    cd py-track/docs
    make html
    firefox/chrome/open/safari py-track/docs/build/index.html