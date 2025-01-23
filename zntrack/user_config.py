"""User configurations."""

# For "node-meta.json" and "dvc stage add ... --metrics-no-cache" the default is using
#  git tracked files. Setting this to True will override the default behavior to always
#  use the DVC cache. If you have a DVC cache setup, this might be desirable, to avoid
#  a mixture between DVC cache and git tracked files.
ALWAYS_CACHE: bool = False
