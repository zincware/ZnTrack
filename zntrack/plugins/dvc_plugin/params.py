import dataclasses

import znflow

from zntrack.config import (
    FIELD_TYPE,
    FieldTypes,
)
from zntrack.node import Node
from zntrack.utils import module_handler


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
    dc_params = dataclasses.asdict(object)
    for f in exclude_fields:
        dc_params.pop(f)
    dc_params["_cls"] = f"{module_handler(object)}.{object.__class__.__name__}"
    return dc_params


def deps_to_params(self, field):
    if getattr(self.node, field.name) is None:
        return
    content = getattr(self.node, field.name)
    if isinstance(content, (list, tuple, dict)):
        new_content = []
        for val in content if isinstance(content, (list, tuple)) else content.values():
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
                    f" field '{field.name}' in list"
                )
        if len(new_content) > 0:
            return new_content
    elif dataclasses.is_dataclass(content) and not isinstance(
        content, (Node, znflow.Connection, znflow.CombinedConnections)
    ):
        return _dataclass_to_dict(content)
    elif isinstance(content, (znflow.Connection, znflow.CombinedConnections)):
        return
    else:
        raise ValueError(
            f"Found unsupported type '{type(content)}' ({content})"
            f" for DEPS field '{field.name}'"
        )
