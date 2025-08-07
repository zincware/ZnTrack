"""Auto-inference system for zntrack fields during serialization/deserialization."""

from zntrack.config import FieldTypes, FIELD_TYPE


def infer_field_type(value) -> FieldTypes:
    """
    Infer whether a value should be treated as params or deps.
    
    This function is called during serialization to determine whether
    a field value should be stored as a parameter or dependency.
    """
    import dataclasses
    import znflow
    from zntrack.node import Node
    
    # Check if it's a znflow connection or combined connection
    if isinstance(value, (znflow.Connection, znflow.CombinedConnections)):
        return FieldTypes.DEPS
    
    # Check if it's a zntrack Node instance
    if isinstance(value, Node):
        return FieldTypes.DEPS
    
    # Check if it's a dataclass (but not a Node) - treat as PARAMS for serialization
    # Dataclasses can be serialized to params.yaml with special _cls metadata
    if dataclasses.is_dataclass(value) and not isinstance(value, Node):
        return FieldTypes.PARAMS
    
    # Check if it's a list/collection containing nodes or connections
    if isinstance(value, (list, tuple)):
        for item in value:
            if isinstance(item, (znflow.Connection, znflow.CombinedConnections, Node)):
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