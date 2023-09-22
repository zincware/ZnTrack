"""Deprecated module for 'zntrack.dvc.<option>' fields.'.

All relevant code has been moved to 'zntrack.fields.dvc.options'
"""


import typing_extensions as tyex

from zntrack.fields import fields
from zntrack.fields.dvc.options import DVCOption


@tyex.deprecated("Use 'zntrack.outs_path' instead.")
def outs(*args, **kwargs) -> DVCOption:
    """Create a outs field."""
    return fields.outs_path(*args, **kwargs)


@tyex.deprecated("Use 'zntrack.params_path' instead.")
def params(*args, **kwargs) -> DVCOption:
    """Create a params field."""
    return fields.params_path(*args, **kwargs)


@tyex.deprecated("Use 'zntrack.deps_path' instead.")
def deps(*args, **kwargs) -> DVCOption:
    """Create a deps field."""
    return fields.deps_path(*args, **kwargs)


@tyex.deprecated("Use 'zntrack.outs_path' instead.")
def outs_no_cache(*args, **kwargs) -> DVCOption:
    """Create a outs_no_cache field."""
    return fields.outs_path(*args, dvc_option="outs-no-cache", **kwargs)


@tyex.deprecated("Use 'zntrack.outs_path' instead.")
def outs_persistent(*args, **kwargs) -> DVCOption:
    """Create a outs_persistent field."""
    return fields.outs_path(*args, dvc_option="outs-persistent", **kwargs)


@tyex.deprecated("Use 'zntrack.metrics_path' instead.")
def metrics(*args, **kwargs) -> DVCOption:
    """Create a metrics field."""
    return fields.metrics_path(*args, **kwargs)


@tyex.deprecated("Use 'zntrack.metrics_path' instead.")
def metrics_no_cache(*args, **kwargs) -> DVCOption:
    """Create a metrics_no_cache field."""
    return fields.metrics_path(*args, dvc_option="metrics-no-cache", **kwargs)


@tyex.deprecated("Use 'zntrack.plots_path' instead.")
def plots(*args, **kwargs) -> DVCOption:
    """Create a plots field."""
    return fields.plots_path(*args, **kwargs)


@tyex.deprecated("Use 'zntrack.plots_path' instead.")
def plots_no_cache(*args, **kwargs) -> DVCOption:
    """Create a plots_no_cache field."""
    return fields.plots_path(*args, dvc_option="plots-no-cache", **kwargs)
