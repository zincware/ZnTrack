import contextlib
import dataclasses
import pathlib
import typing as t

import aim
import dvc.repo
import git

from zntrack.config import PLUGIN_EMPTY_RETRUN_VALUE, ZNTRACK_OPTION, ZnTrackOptionEnum
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
            run["git_remote"] = pathlib.Path.cwd().as_posix()
            run["git_hash"] = None
            run["git_commit_message"] = None
            run["dvc_node"] = f"{self.node.__module__}.{self.node.__class__.__name__}"
            run["dvc_name"] = self.node.name
            # add a tag for the node
            run.add_tag(self.node.__class__.__name__)

        return run

    def convert_to_dvc_yaml(self):
        return PLUGIN_EMPTY_RETRUN_VALUE

    def convert_to_params_yaml(self):
        return PLUGIN_EMPTY_RETRUN_VALUE

    def convert_to_zntrack_json(self):
        return PLUGIN_EMPTY_RETRUN_VALUE

    @classmethod
    def finalize(cls, rev: str | None = None):
        """Update the aim run to include the correct commit data.

        Run this, once you have created a commit for your DVC experiment.
        This will update the aim run with the correct git hash, message and remote.

        Parameters
        ----------
        rev : str, optional
            The git revision to use. If None, 'HEAD' will be used.

        Example:
        -------
        python -c "from zntrack.plugins.aim_plugin import AIMPlugin; AIMPlugin.finalize()"

        """
        import zntrack

        repo = git.Repo(".")

        if rev is None:
            commit_hash = repo.head.commit.hexsha
            commit_message = repo.head.commit.message
        else:
            commit_hash = repo.commit(rev).hexsha
            commit_message = repo.commit(rev).message

        # get the default remote for the current branch
        remote = repo.remote()

        node_names = []
        with dvc.repo.Repo(rev=rev) as repo:
            for stage in repo.index.stages:
                node_names.append(stage.name)
        for node_name in node_names:
            node = zntrack.from_rev(node_name, rev=rev)
            plugin = cls(node)
            run = plugin.get_aim_run()
            run["git_hash"] = commit_hash
            run["git_commit_message"] = commit_message
            run["git_remote"] = remote.url
