Overview
========

PyTrack is designed as an object oriented mapper for `DVC <https://dvc.org/>`_.
DVC provides tracking of large data files within a GIT repository.
Therefore all PyTrack instances will later be executed inside a GIT repository.
Furthermore, DVC provides method for building a dependency graph, tracking parameters, comparing metrics and querying multiple runs.

**Why does it need an object oriented mapper?**

Whilst DVC provides all this functionality it is designed to be programming language independent. PyTrack is designed purely for building python packages and is optimized in such manner.

Stages
------
DVC organizes its pipeline in multiple stages (see https://dvc.org/doc/start for more information).
In the case of PyTrack every stage inherits from :code:`pytrack.PyTrack` as follows

.. code-block:: python

    from pytrack import PyTrack

    class Stage(PyTrack):

        def __init__(self, id_=None, filter_=None):
            super().__init__(id_, filter_)
            self.post_init(id_, filter_)

        def __call__(self):
            self.parameters = {}
            self.post_call()

        def run(self):
            self.results = self.parameters

This example defines a DVC stage that has no dependencies and no parameters.
To use the stage we have to move it inside a directory and initialize :code:`git init` and :code:`dvc init`
If we now instantiate a stage and call it :code:`Stage()()` three important files will be generated for us:

dvc.yaml
^^^^^^^^

The first file we are interested in defines all DVC stage :code:`dvc.yaml`

.. code-block:: yaml

    stages:
      Stage_0:
        cmd: python3 -c "from dvc_stages import Stage; Stage(id_=0).run()"
        params:
        - config/params.json:
          - Stage.0
        outs:
        - outs/0_Stage.json

We can see here that DVC will run :code:`python3 -c "from dvc_stages import Stage; Stage(id_=0).run()"`.
This requires that all information for running this command must be given through files.
It is crucial that this command can run without requiring anything being passed to the :code:`__init__` of the class!
This file also specifies the dependencies and outputs from our stage. This information can then be used to generate e.g., the DAG.

params.json
^^^^^^^^^^^

Most of the configurations (everything passed to :code:`self.parameters`) is stored in `params.json`.
Because no parameters are passed this file currently looks like

.. code-block:: json

    {
        "Stage": {
            "0": {}
        }
    }

Here :code:`Stage` gives the name of Stage, which is usually the name of the class.
Therefore it is important that :code:`PyTrack` stages don't share a name within one pipeline.
The :code:`id = 0` allows for having multiple parameters to a single stage. This is usually not a good idea and therefore 0 is handled as the default.

0_Stages.json
^^^^^^^^^^^^^

The file :code:`outs/0_Stage.json` is the output from the stage.
Its content is equivalent to :code:`Stage(id_=0).results` after running the stage.
This allows accessing and sharing the result of a stage without manually opening the generated files.
In general all paths should be handled through PyTrack in a way described later.


DVCParams
---------

Usually one does like to interact with different files and might also generate different outputs.
PyTrack has a :code:`from pytrack import DVCParams` prepared for this.
It supports all arguments from https://dvc.org/doc/command-reference/run#options