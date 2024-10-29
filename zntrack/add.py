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
    force: bool = False

    def run(self):
        if self.path.exists() and not self.force:
            dvc_file = self.path.parent / (self.path.name + ".dvc")
            if dvc_file.exists():
                return
            else:
                raise FileExistsError(f"{self.path} exists but no {dvc_file} file found")
        if self.rev:
            cmd = [
                "dvc",
                "import",
                self.url,
                self.path.as_posix(),
                "--rev",
                self.rev,
                "--no-exec",
            ]
            if self.force:
                cmd.append("--force")
            subprocess.check_call(cmd)
        else:
            cmd = ["dvc", "import-url", self.url, self.path.as_posix(), "--no-exec"]
            if self.force:
                cmd.append("--force")
            subprocess.check_call(cmd)


def add(
    url: str, path: str, rev: t.Optional[str] = None, force: bool = False
) -> DVCImportPath:
    return DVCImportPath(url, pathlib.Path(path), rev, force=force)
