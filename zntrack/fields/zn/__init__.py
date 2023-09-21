"""Deprecated module for 'zntrack.zn.<option>' fields.'.

All relevant code has been moved to 'zntrack.fields.zn.options'
"""

import typing_extensions as tyex

from zntrack.fields import fields


@tyex.deprecated("Use 'zntrack.params' instead.")
def params(*args, **kwargs):
    """Create a params field."""
    return fields.params(*args, **kwargs)


@tyex.deprecated("Use 'zntrack.deps' instead.")
def deps(*args, **kwargs):
    """Create a dependency field."""
    return fields.deps(*args, **kwargs)


@tyex.deprecated("Use 'zntrack.outs' instead.")
def outs():
    """Create an output field."""
    return fields.outs()


@tyex.deprecated("Use 'zntrack.metrics' instead.")
def metrics():
    """Create a metrics output field."""
    return fields.metrics()


@tyex.deprecated("Use 'zntrack.plots' instead.")
def plots(*args, **kwargs):
    """Create a metrics output field."""
    return fields.plots(*args, **kwargs)


@tyex.deprecated("Use 'zntrack.deps' instead.")
def nodes(*args, **kwargs):
    """Create a node field."""
    return fields.deps(*args, **kwargs)
