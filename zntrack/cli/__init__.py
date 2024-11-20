from zntrack.cli.cli import app

__all__ = ["app"]

try:
    from zntrack.cli.mlflow import mlflow_sync

    __all__.append("mlflow_sync")
except ImportError:
    pass
