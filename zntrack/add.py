import pathlib
import typing as t
import dataclasses
import subprocess
from znflow.node import NodeBaseMixin

PATH_LIKE = t.Union[str, pathlib.Path]


@dataclasses.dataclass(frozen=True)
class DVCImportPath(NodeBaseMixin):
    url: str
    path: pathlib.Path
    rev: str | None = None

    def run(self):
        if self.rev:
            subprocess.check_call(["dvc", "import", self.url, self.path.as_posix(), "--rev", self.rev, "--no-exec"])
        else:
            subprocess.check_call(["dvc", "import-url", self.url, self.path.as_posix(), "--no-exec"])


def add(url: str, path: str, rev: t.Optional[str] = None) -> DVCImportPath:
    return DVCImportPath(url, pathlib.Path(path), rev)
