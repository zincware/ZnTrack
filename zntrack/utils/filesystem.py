"""Filesystem utilities for ZnTrack."""

import pathlib
from typing import Union


def resolve_dvc_path(
    fs, state_path: pathlib.Path, target_path: Union[str, pathlib.Path]
) -> Union[str, pathlib.Path]:
    """Resolve a path for DVCFileSystem, handling relative/absolute path conversion.

    DVCFileSystem expects paths relative to the repository root, but ZnTrack often
    works with absolute paths. This function handles the conversion.

    Args:
        fs: The filesystem object (DVCFileSystem or LocalFileSystem)
        state_path: The state path of the node
        target_path: The target path to resolve (can be str or Path)

    Returns:
        Resolved path suitable for the filesystem (str for DVCFileSystem, Path for local)
    """
    # For non-DVC filesystems, return the original path
    if not hasattr(fs, "repo") or not getattr(fs, "repo", None):
        return target_path

    # For DVCFileSystem, convert to relative path
    repo_root = pathlib.Path(fs.repo.root_dir)
    target_path = pathlib.Path(target_path)

    # If target_path is already relative, combine with state_path if needed
    if not target_path.is_absolute():
        if state_path.is_absolute():
            # Make state_path relative to repo_root first
            try:
                relative_state = state_path.relative_to(repo_root)
                final_path = relative_state / target_path
            except ValueError:
                # If state_path can't be made relative, use absolute target_path
                final_path = target_path
        else:
            # Both are relative
            final_path = state_path / target_path
    else:
        # target_path is absolute, make it relative to repo_root
        try:
            final_path = target_path.relative_to(repo_root)
        except ValueError:
            # If target_path can't be made relative to repo_root, use as-is
            final_path = target_path

    return str(final_path)


def resolve_state_file_path(
    fs, state_path: pathlib.Path, filename: str, validate_exists: bool = False
) -> Union[str, pathlib.Path]:
    """Resolve a path to a state file for the given filesystem.

    Handles params.yaml, zntrack.json, etc.

    Args:
        fs: The filesystem object
        state_path: The state path of the node
        filename: The filename to resolve (e.g., "params.yaml", "zntrack.json")
        validate_exists: Whether to validate that the path exists before returning

    Returns:
        Resolved path suitable for the filesystem

    Raises:
        FileNotFoundError: If validate_exists is True and the resolved path doesn't exist
    """
    target_path = state_path / filename
    resolved_path = resolve_dvc_path(fs, state_path, target_path)

    # Optionally validate that the path exists before returning it
    # This provides early error detection for missing files when requested
    if validate_exists and hasattr(fs, "exists") and not fs.exists(resolved_path):
        raise FileNotFoundError(f"State file not found: {resolved_path}")

    return resolved_path
