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
In the case of PyTrack every stage is decorated with :code:`pytrack.pytrack` as follows

.. code-block:: python

    from pytrack import pytrack, parameter, result


    @pytrack
    class Stage:
        def __init__(self):
            """Class constructor

            Definition of parameters and results
            """
            self.n_1 = parameter()
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
            """Actual computation
            """
            self.sum = self.n_1 + self.n_2
            self.dif = self.n_1 - self.n_2

This example defines a DVC stage that performs an addition and subtraction on two numbers :code:`n_1, n_2`.
To use the stage we have to move it inside a directory and initialize :code:`git init` and :code:`dvc init`
If we now instantiate a stage and call it :code:`Stage()(5, 10)` three important files will be generated for us:

dvc.yaml
^^^^^^^^

The first file we are interested in defines all DVC stage :code:`dvc.yaml`

.. code-block:: yaml

    stages:
      Stage_0:
        cmd: python -c "from dvc_stages import Stage; Stage(id_=0).run()"
        params:
        - config/params.json:
          - Stage.0
        outs:
        - outs\0_Stage.json

In this scenario we put the definition in a file :code:`dvc_stages.py`.
We can see here that DVC will run :code:`python3 -c "from dvc_stages import Stage; Stage(id_=0).run()"`.
This requires that all information for running this command must be given through files.
It is crucial that this command can run without requiring anything being passed to the :code:`__init__` of the class!
Furthermore, we see here that we pass the argument :code:`id_=0` which is not defined in our :code:`__init__` because PyTrack handles this for us automatically.
This file also specifies the dependencies and outputs from our stage. This information can then be used to generate e.g., the DAG.

params.json
^^^^^^^^^^^

All :code:`parameter()` are stored in `params.json`.
Our file contains two numbers an looks as follows

.. code-block:: json

    {
        "Stage": {
            "0": {
                "n_1": 50,
                "n_2": 100
            }
        }
    }

Here :code:`Stage` gives the name of Stage, which is usually the name of the class.
Therefore it is important that :code:`PyTrack` stages don't share a name within one pipeline.
The :code:`id = 0` allows for having multiple parameters to a single stage.
This is usually not a good idea and therefore 0 is handled as the default.

0_Stages.json
^^^^^^^^^^^^^

The file :code:`outs/0_Stage.json` is the output from the stage.
It contains the values for :code:`Stage(id_=0).sum` and :code:`Stage(id_=0).dif` after running the stage.
PyTrack needs to know which attributes are considered results and therefore has the definition of :code:`result()` in the init.
This allows accessing and sharing the result of a stage without manually opening the generated files.
In general all paths should be handled through PyTrack in a way described later.

We can use :code:`dvc repro` or the following code snippet to run our stage

.. code-block:: python

    from dvc_stages import Stage
    from pytrack import PyTrackProject

    project = PyTrackProject()
    project.create_dvc_repository()

    stage = Stage()
    stage(5, 10)
    project.name = "Test1"
    project.run()

This will create the :code:`outs/0_Stage.json` as

.. code-block:: json

    {
        "sum": 150,
        "dif": -50
    }

which we can also access now via

.. code-block:: python

    from dvc_stages import Stage
    from pytrack import PyTrackProject

    project = PyTrackProject()
    project.name = "Test1"
    project.load()

    stage = Stage(id_=0)
    print(stage.sum)
    print(stage.dif)

Storing and managing the data is handled by PyTrack allowing the usage as an almost normal python class.


DVCParams
---------

Usually one does like to interact with different files and might also generate different outputs.
PyTrack has a :code:`from pytrack import DVCParams` prepared for this.
It supports all arguments from https://dvc.org/doc/command-reference/run#options

For a better understanding we will look at a quick example.
We read the text of a dependency file and write it to another file specified as an output.
The PyTrack stage could look like the following:

.. code-block:: python

    from pytrack import pytrack, DVCParams

    @pytrack
    class StageIO:
        def __init__(self):
            """Class constructor

            Definition of parameters and results
            """
            self.dvc = DVCParams(outs=['calculation.txt'])

        def __call__(self, file):
            """User input

            Parameters
            ----------
            file: str,
                Path to the file we want to read
            """

            self.dvc.deps.append(file)

        def run(self):
            """Actual computation
            """

            with open(self.dvc.deps[0], "r") as f:
                file_content = f.readlines()

            self.dvc.outs[0].write_text("".join(file_content))

We define an output in the init with :code:`self.dvc = DVCParams(outs=['calculation.txt'])`.
In principle we could also do that in the :code:`__call__` but it must be set to :code:`self.dvc`!
Then we ask the user to add a path to the file we want to read and add that as a dependency :code:`self.dvc.deps.append(file)`.
Now we are able to access those values in the :code:`run` method to read and write to them.
We can also access the outs later via

.. code-block:: python

    from dvc_stages import StageIO

    stage_io = StageIO(id_=0)
    print(stage_io.dvc.outs[0].read_text())

It is worth mentioning that PyTrack associates a folder with the out files and usually stores them in :code:`/outs`
which is also represented in the :code:`dvc.yaml`

.. code-block:: yaml

    stages:
      StageIO_0:
        cmd: python -c "from dvc_stages import StageIO; StageIO(id_=0).run()"
        deps:
        - dvc_stages.py
        params:
        - config/params.json:
          - StageIO.0
        outs:
        - outs\0_calculation.txt

Building a Pipeline
-------------------

Now that we know how to define parameters, results, dependencies and outputs we can join them together to build a DAG.
Therefore we need to use the output of one stage as the dependency of the next stage.