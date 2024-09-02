import contextlib
import dataclasses
import typing as t

import aim

from zntrack.config import (
    PLUGIN_EMPTY_RETRUN_VALUE,
    ZNTRACK_OPTION,
    ZnTrackOptionEnum,
)
from zntrack.plugins import ZnTrackPlugin

if t.TYPE_CHECKING:
    pass


class AIMPlugin(ZnTrackPlugin):
    def getter(self, field: dataclasses.Field) -> t.Any:
        # The AIM plugin relies on others, e.g. DVCPlugin for loading/saving data
        return PLUGIN_EMPTY_RETRUN_VALUE

    def save(self, field: dataclasses.Field) -> None:
        if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.PARAMS:
            run = self.get_aim_run()
            run[field.name] = getattr(self.node, field.name)
        if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.METRICS:
            run = self.get_aim_run()

            assert isinstance(getattr(self.node, field.name), dict)

            for key, value in getattr(self.node, field.name).items():
                run.track(value, name=f"{field.name}.{key}")

    def get_aim_run(self) -> aim.Run:
        uid = self.node.state.get_stage_hash()
        repo = aim.Repo(path=".")
        run_hash = None

        with contextlib.suppress(Exception):
            # if aim throws some error, we assuem the run does not exist
            # and we create a new one with `run_hash = None`
            for run_metrics_col in repo.query_metrics(
                f"run.dvc_stage_hash == '{uid}'"
            ).iter():
                run_hash = run_metrics_col.run.hash
                break
        run = aim.Run(run_hash=run_hash)
        if run_hash is None:
            run["dvc_stage_hash"] = uid
        return run
