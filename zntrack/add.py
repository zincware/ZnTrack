import dataclasses
import pathlib
import subprocess
import typing as t

from znflow.node import NodeBaseMixin

PATH_LIKE = t.Union[str, pathlib.Path]


@dataclasses.dataclass(frozen=True)
class DVCImportPath(NodeBaseMixin):
    url: str
    path: pathlib.Path
    rev: str | None = None

    def run(self):
        if self.path.exists():
            # check if a {self.path}.dvc file exists
            if (self.path.with_suffix(".dvc")).exists():
                return
            else:
                raise FileExistsError(
                    f"{self.path} exists but no {self.path}.dvc file found"
                )
        if self.rev:
            subprocess.check_call(
                [
                    "dvc",
                    "import",
                    self.url,
                    self.path.as_posix(),
                    "--rev",
                    self.rev,
                    "--no-exec",
                ]
            )
        else:
            subprocess.check_call(
                ["dvc", "import-url", self.url, self.path.as_posix(), "--no-exec"]
            )


def add(url: str, path: str, rev: t.Optional[str] = None) -> DVCImportPath:
    return DVCImportPath(url, pathlib.Path(path), rev)
