import copy
import dataclasses

import znflow

from zntrack.config import (
    FIELD_TYPE,
    FieldTypes,
)
from zntrack.node import Node
from zntrack.utils import module_handler


def _convert_value_recursively(value):
    """Recursively convert values, handling dataclasses in collections."""
    if dataclasses.is_dataclass(value) and not isinstance(
        value, (Node, znflow.Connection, znflow.CombinedConnections)
    ):
        return _dataclass_to_dict(value)
    elif isinstance(value, list):
        return [_convert_value_recursively(item) for item in value]
    elif isinstance(value, tuple):
        return tuple(_convert_value_recursively(item) for item in value)
    elif isinstance(value, set):
        # Sets cannot contain dicts (unhashable), so convert to list
        return [_convert_value_recursively(item) for item in value]
    elif isinstance(value, dict):
        return {k: _convert_value_recursively(v) for k, v in value.items()}
    else:
        return copy.deepcopy(value)


def _dataclass_to_dict(object) -> dict:
    """Convert a dataclass to a dictionary excluding certain keys."""
    exclude_fields = []
    for field in dataclasses.fields(object):
        if FIELD_TYPE in field.metadata:
            if field.metadata[FIELD_TYPE] in [
                FieldTypes.PARAMS_PATH,
                FieldTypes.DEPS_PATH,
                # FieldTypes.DEPS,
            ]:
                exclude_fields.append(field.name)
            else:
                raise TypeError(
                    f"Unsupported field type '{field.metadata[FIELD_TYPE]}'"
                    f" for field '{field.name}'."
                )

    # Custom conversion that handles nested dataclasses
    dc_params = {}
    for field in dataclasses.fields(object):
        if field.name in exclude_fields:
            continue

        value = getattr(object, field.name)
        dc_params[field.name] = _convert_value_recursively(value)

    dc_params["_cls"] = f"{module_handler(object)}.{object.__class__.__name__}"
    return dc_params


def deps_to_params(self, field):
    if getattr(self.node, field.name) is None:
        return None
    content = getattr(self.node, field.name)
    if isinstance(content, (list, tuple, set, dict)):
        if isinstance(content, dict):
            # For dicts, we need to convert both keys and values
            new_content = {}
            for key, val in content.items():
                if dataclasses.is_dataclass(val) and not isinstance(
                    val, (Node, znflow.Connection, znflow.CombinedConnections)
                ):
                    new_content[key] = _dataclass_to_dict(val)
                elif isinstance(val, (znflow.Connection, znflow.CombinedConnections)):
                    pass
                else:
                    raise ValueError(
                        f"Found unsupported type '{type(val)}' ({val}) for DEPS"
                        f" field '{field.name}' in dict"
                    )
        else:
            # For lists, tuples, sets
            new_content = []
            for val in content:
                if dataclasses.is_dataclass(val) and not isinstance(
                    val, (Node, znflow.Connection, znflow.CombinedConnections)
                ):
                    # We save the values of the passed dataclasses
                    #  to the params.yaml file to be later used
                    #  by the DataclassContainer to recreate the
                    #  instance with the correct parameters.
                    new_content.append(_dataclass_to_dict(val))
                elif isinstance(val, (znflow.Connection, znflow.CombinedConnections)):
                    pass
                else:
                    raise ValueError(
                        f"Found unsupported type '{type(val)}' ({val}) for DEPS"
                        f" field '{field.name}' in collection"
                    )
            # Preserve the original collection type
            if isinstance(content, tuple):
                new_content = tuple(new_content)
            elif isinstance(content, set):
                # Sets cannot contain dicts (unhashable), so convert to list
                new_content = list(new_content)

        if len(new_content) > 0:
            return new_content
    elif dataclasses.is_dataclass(content) and not isinstance(
        content, (Node, znflow.Connection, znflow.CombinedConnections)
    ):
        return _dataclass_to_dict(content)
    elif isinstance(content, (znflow.Connection, znflow.CombinedConnections)):
        return None
    else:
        raise ValueError(
            f"Found unsupported type '{type(content)}' ({content})"
            f" for DEPS field '{field.name}'"
        )
    return None
