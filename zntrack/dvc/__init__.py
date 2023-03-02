"""Collection of DVC options.

Based on ZnTrackOption python descriptors this gives access to them being used
to define e.g. dependencies

Examples
--------
>>> from zntrack import Node, dvc
>>> class HelloWorld(Node)
>>>     vars = dvc.params()

"""
