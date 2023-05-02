Workflow Management
===================

ZnTrack is build around a few basic principles of a computational workflow (also called graph):

- A workflow is a directed acyclic graph (DAG) of nodes.
- A node is a function that takes a set of inputs and produces a set of outputs.
- A node, once executed with a given set of inputs is considered completed and will not be executed again.

Our goal is, to make writing and using nodes as easy as possible.
Therefore, ZnTrack is designed as a database-free tool written on top of DVC.
This allows to focus on the workflow and not on a complicated setup.

Nodes written in ZnTrack can be used across several projects and can be shared with other users.
Workflows, e.g. how nodes are connected, which parameters are used and which metrics are produced, are stored in git commits.
This allows to track changes in the workflow and to reproduce results at any point in time.
Further information on how they are stored is described in the DVC section.

Example Workflow
----------------

Let's assume we want to fit a model to some data.
Afterwards, we want to analyse the model using some validation dataset.

.. image:: https://mermaid.ink/img/pako:eNp1kc1OwzAQhF-l2nObiJQWlAMSUtQXgBtG1creEqPYRv4pqqq-O1swhMaQi6P5xrsz8hGkUwQt7Ab3Lnv0cfbYCTvLn2V49STg3uJwCLTRUcDzJW4Ys95hxIItmUWP2lYKY6X2snBcs2OPw7-8WSzuPkNMBme5mUwb3ZdgxWvOZ6jHJrWh6LUMW-u2EmVP1Wtwtkiw_rmaW9YuxfC39-Z334Lejl3LLTn5ajIwy-vJpG83zMGQN6gVP-HxbOIAPRkS0PKvoh2mgbcJe2IrpugeDlZCG32iOaQ3jkKdxheP5ks8fQCw0qCO?type=png
    :alt: mermaid diagram

The workflow consists of our inputs ``train.dat`` and ``val.dat`` and two nodes ``FitData`` and ``AnalyseFit``.
Another way at representing this workflow is by printing the outputs of the nodes.

We can define this workflow by creating two Python functions *or* classes for ``FitData`` and ``AnalyseFit``.
They can be connected directly forming the graphs above.

Defining Nodes is show in the ZnTrack API sections on functions :ref:`userdoc-get-started-api_functions` and classes :ref:`userdoc-get-started-api_classes`.
