"""Filesystem utilities for ZnTrack."""

import pathlib
from typing import Union


def resolve_dvc_path(
    fs, state_path: pathlib.Path, target_path: Union[str, pathlib.Path]
) -> Union[str, pathlib.Path]:
    """Resolve a path for DVCFileSystem, handling relative/absolute path conversion."""

    if not hasattr(fs, "repo") or not getattr(fs, "repo", None):
        return target_path

    repo_root = pathlib.Path(fs.repo.root_dir).resolve()
    target_path = pathlib.Path(target_path)

    if target_path.is_absolute():
        try:
            # Convert absolute path to relative to repo root
            final_path = target_path.resolve().relative_to(repo_root)
        except ValueError:
            # Outside of repo, return as-is
            final_path = target_path
    else:
        # Already relative — assume it's correctly relative to the repo root
        final_path = target_path

    print(f"Resolving DVC path: {target_path} relative to {repo_root} -> {final_path}")
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
