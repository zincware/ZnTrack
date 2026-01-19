"""Auto-inference system for zntrack fields during serialization/deserialization."""

import dataclasses
import json
import logging

import yaml

from zntrack.config import FIELD_TYPE, ZNTRACK_LAZY_VALUE, FieldTypes

log = logging.getLogger(__name__)


def infer_field_type(value) -> FieldTypes:
    """
    Infer whether a value should be treated as params or deps.

    This function is called during serialization to determine whether
    a field value should be stored as a parameter or dependency.
    """
    import dataclasses

    import znflow

    # Check if it's a znflow connection or combined connection
    if isinstance(value, (znflow.Connection, znflow.CombinedConnections)):
        return FieldTypes.DEPS

    # Check if its a dataclass / zntrack.Node
    if dataclasses.is_dataclass(value):
        return FieldTypes.DEPS

    # Check if it's a list/collection containing nodes or connections
    if isinstance(value, (list, tuple)):
        for item in value:
            if isinstance(item, (znflow.Connection, znflow.CombinedConnections)):
                return FieldTypes.DEPS
            if dataclasses.is_dataclass(item):
                return FieldTypes.DEPS
        # If list contains only dataclasses and/or primitives, treat as PARAMS
        # (dataclasses can be serialized to params.yaml)

    # For primitive types and basic collections, treat as params
    return FieldTypes.PARAMS


def is_auto_inferred_field(cls, field_name: str) -> bool:
    """
    Check if a field should use auto-inference.

    Returns True if:
    1. Field is annotated but has no explicit zntrack field definition
    2. Field is not a special zntrack field (name, etc.)
    """
    # Skip special fields
    from zntrack.node import Node

    if field_name in Node()._protected_:
        return False

    # Check if field is annotated
    if not hasattr(cls, "__annotations__") or field_name not in cls.__annotations__:
        return False

    # For dataclass fields, we need to check the field metadata
    import dataclasses

    if dataclasses.is_dataclass(cls):
        for field in dataclasses.fields(cls):
            if field.name == field_name:
                # Check if it has zntrack field metadata
                if FIELD_TYPE in field.metadata:
                    return False
                # This is an annotated field without explicit zntrack metadata
                return True

    return False


def update_auto_inferred_fields(cls, path, name, lazy_values, _fs):
    """
    Replace auto-inferred fields with zntrack.params/zntrack.deps.

    This function processes dataclass fields to automatically infer whether they should be
    treated as parameters or dependencies in the zntrack system. It preserves original
    metadata for all other fields, including fields with init=False.

    Parameters
    ----------
    cls : type
        The dataclass to update with auto-inferred fields.
    path : pathlib.Path or str
        Path to the directory containing the params.yaml file.
    name : str
        Name identifier used to look up parameters in the params.yaml file.
    lazy_values : dict
        Dictionary to store lazy value markers for fields that need lazy evaluation.
    _fs : FileSystem
        File system interface for reading the params.yaml file.

    Returns
    -------
    type
        The updated class with auto-inferred fields properly configured.

    Notes
    -----
    The function performs the following steps:
    1. Checks if any fields need auto-inference
    2. Reads existing parameters from params.yaml if available
    3. For each field:
       - Skips protected fields while preserving their metadata
       - Auto-infers field type based on presence of "_cls" in parameters
       - Preserves original field metadata for non-inferred fields
    4. Recreates the dataclass if auto-inferred fields were added

    Fields are inferred as:
    - `zntrack.deps()` if the field contains "_cls" in its serialized form
    - `zntrack.params()` otherwise

    Examples
    --------
    >>> import dataclasses
    >>> from pathlib import Path
    >>>
    >>> @dataclasses.dataclass
    ... class MyNode:
    ...     value: int = 5
    ...     reference: object = None
    >>>
    >>> lazy_vals = {}
    >>> updated_cls = update_auto_inferred_fields(
    ...     MyNode, Path("./data"), "my_node", lazy_vals, fs
    ... )
    """
    from zntrack import Node

    # Determine protected fields to skip
    protected_fields = Node()._protected_ | {"always_changed", "nwd", "name"}

    # Check if update is needed
    needs_update = _check_needs_update(cls, protected_fields)

    if not needs_update:
        _set_lazy_values_only(cls, lazy_values, protected_fields)
        return cls

    # Process fields with auto-inference
    auto_inferred_exists = False
    original_fields = {f.name: f for f in dataclasses.fields(cls)}
    params = _load_params(path, name, _fs)

    for field in dataclasses.fields(cls):
        if field.name in protected_fields:
            # Preserve protected field metadata
            _preserve_field(cls, field, original_fields)
            continue

        if field.init:
            lazy_values[field.name] = ZNTRACK_LAZY_VALUE

            if field.metadata.get(FIELD_TYPE) is None:
                auto_inferred_exists = True
                _infer_and_set_field_type(cls, field, params, name)
                continue

        # Preserve non-inferred fields
        _preserve_field(cls, field, original_fields)

    # Recreate dataclass if modifications were made
    if auto_inferred_exists:
        cls = dataclasses.dataclass(cls, kw_only=True)

    return cls


def _check_needs_update(cls, protected_fields):
    """
    Check if any fields require auto-inference.

    Parameters
    ----------
    cls : type
        The dataclass to check.
    protected_fields : set
        Set of field names that should be skipped.

    Returns
    -------
    bool
        True if update is needed, False otherwise.
    """
    return any(
        f.init and f.metadata.get(FIELD_TYPE) is None and f.name not in protected_fields
        for f in dataclasses.fields(cls)
    )


def _set_lazy_values_only(cls, lazy_values, protected_fields):
    """
    Set lazy values for eligible fields without modifying the class.

    Parameters
    ----------
    cls : type
        The dataclass to process.
    lazy_values : dict
        Dictionary to store lazy value markers.
    protected_fields : set
        Set of field names that should be skipped.
    """
    for field in dataclasses.fields(cls):
        if field.init and field.name not in protected_fields:
            lazy_values[field.name] = ZNTRACK_LAZY_VALUE


def _load_params(path, name, _fs):
    """
    Load parameters from params.yaml file.

    Parameters
    ----------
    path : pathlib.Path or str
        Path to the directory containing params.yaml.
    name : str
        Name identifier for parameter lookup.
    _fs : FileSystem
        File system interface.

    Returns
    -------
    dict
        Parameters dictionary, empty dict if file not found.
    """
    try:
        with _fs.open(path / "params.yaml") as stream:
            params = yaml.safe_load(stream) or {}
    except FileNotFoundError:
        params = {}
    return params


def _preserve_field(cls, field, original_fields):
    """
    Preserve original field and its metadata on the class.

    Parameters
    ----------
    cls : type
        The class to update.
    field : dataclasses.Field
        The field to preserve.
    original_fields : dict
        Mapping of field names to original field objects.
    """
    setattr(cls, field.name, original_fields[field.name])
    cls.__annotations__[field.name] = field.type


def _infer_and_set_field_type(cls, field, params, name):
    """
    Infer field type from parameters and set appropriate zntrack field.

    Parameters
    ----------
    cls : type
        The class to update.
    field : dataclasses.Field
        The field to process.
    params : dict
        Parameters loaded from params.yaml.
    name : str
        Name identifier for parameter lookup.
    """
    import zntrack

    field_value = params.get(name, {}).get(field.name)

    if field_value is not None and "_cls" in json.dumps(field_value):
        setattr(cls, field.name, zntrack.deps())
        log.debug(f"Auto-inferred field '{name}.{field.name}' set to 'deps'")
    else:
        # Default to deps if no params found, otherwise params
        if field_value is None:
            setattr(cls, field.name, zntrack.deps())
            log.debug(f"Auto-inferred field '{name}.{field.name}' set to 'deps'")
        else:
            setattr(cls, field.name, zntrack.params())
            log.debug(f"Auto-inferred field '{name}.{field.name}' set to 'params'")

    # Preserve type annotation
    cls.__annotations__[field.name] = field.type
