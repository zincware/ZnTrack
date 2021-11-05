Installation
============

ZnTrack can be most easily installed via pip:

.. code-block:: bash

    pip install zntrack

If you want to install ZnTrack from source you can use

.. code-block:: bash

    git clone https://github.com/zincware/ZnTrack.git
    cd ZnTrack
    pip install .

If you are a developer we suggest using

.. code-block:: bash

    pip install -e .

If you have cloned the repository you might be interested in building the docs
locally.
This can be done as follows:

.. code-block:: bash

    cd ZnTrack/docs
    make html
    firefox/chrome/open/safari ZnTrack/docs/build/index.html

If you are using conda and having issues with :code:`pandoc` you might be able to
resolve them using :code:`conda install pandoc`.