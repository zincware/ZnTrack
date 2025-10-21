"""Test that YAML output does not contain anchor references."""

import yaml

from zntrack.plugins.base import _NoAnchorDumper


def test_no_anchor_dumper():
    """Test that _NoAnchorDumper prevents anchor generation."""
    
    # Create data that would normally trigger anchor references
    repeated_list = [1, 1, 1]
    data_with_refs = {
        'repeat': repeated_list,
        'another_repeat': repeated_list
    }
    
    # Test with standard YAML dumper (should create anchors)
    standard_output = yaml.safe_dump(data_with_refs)
    assert '&id' in standard_output, "Standard dumper should create anchor references"
    
    # Test with NoAnchorDumper
    no_anchor_output = yaml.dump(data_with_refs, Dumper=_NoAnchorDumper)
    assert '&id' not in no_anchor_output, "NoAnchorDumper should not create anchor references"
    assert '*id' not in no_anchor_output, "NoAnchorDumper should not create alias references"
    
    # Verify semantic equivalence
    standard_parsed = yaml.safe_load(standard_output)
    no_anchor_parsed = yaml.safe_load(no_anchor_output)
    
    assert standard_parsed == no_anchor_parsed, "All outputs should be semantically equivalent"


def test_yaml_content_preservation():
    """Test that the fix preserves the original data structure."""
    
    # Test with nested structures that could create anchors
    shared_dict = {'temperature': 300, 'friction': 0.1}
    complex_data = {
        'thermostat1': shared_dict,
        'thermostat2': shared_dict,
        'steps': 100,
        'nested': {
            'repeat_values': [1, 1, 1],
            'same_values': [1, 1, 1]  # Different object, same content
        }
    }
    
    # Use NoAnchorDumper
    output = yaml.dump(complex_data, Dumper=_NoAnchorDumper)
    
    # Verify no anchors
    assert '&id' not in output, "Should not contain anchor references"
    assert '*id' not in output, "Should not contain alias references"
    
    # Verify content is preserved
    parsed = yaml.safe_load(output)
    assert parsed['thermostat1']['temperature'] == 300
    assert parsed['thermostat2']['friction'] == 0.1
    assert parsed['steps'] == 100
    assert parsed['nested']['repeat_values'] == [1, 1, 1]


def test_edge_cases():
    """Test edge cases that might cause issues."""
    
    # Empty data
    empty_output = yaml.dump({}, Dumper=_NoAnchorDumper)
    assert '&id' not in empty_output
    
    # Single values
    single_output = yaml.dump({'value': 42}, Dumper=_NoAnchorDumper)
    assert '&id' not in single_output
    
    # None values
    none_output = yaml.dump({'value': None}, Dumper=_NoAnchorDumper)
    assert '&id' not in none_output
    
    # Boolean values
    bool_output = yaml.dump({'flag': True, 'other_flag': False}, Dumper=_NoAnchorDumper)
    assert '&id' not in bool_output