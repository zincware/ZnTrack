import contextlib
import dataclasses
import os
import pathlib
import typing as t

import aim
import dvc.repo
import git

from zntrack.config import PLUGIN_EMPTY_RETRUN_VALUE, ZNTRACK_OPTION, ZnTrackOptionEnum
from zntrack.plugins import ZnTrackPlugin, get_exp_info, set_exp_info
from zntrack.utils.misc import load_env_vars

if t.TYPE_CHECKING:
    pass


class AIMPlugin(ZnTrackPlugin):

    _continue_on_error_ = True

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

    def get_aim_run(self, read_only: bool = False, reset: bool = False) -> aim.Run:
        load_env_vars()

        path = os.environ.get("AIM_TRACKING_URI")

        if not reset:
            try:
                return self.aim_run
            except AttributeError:
                pass

        uid = self.node.state.get_stage_hash()
        repo = aim.Repo(path=path)
        run_hash = None

        with contextlib.suppress(Exception):
            # if aim throws some error, we assuem the run does not exist
            # and we create a new one with `run_hash = None`
            for run_metrics_col in repo.query_metrics(
                f"run.dvc_stage_hash == '{uid}'"
            ).iter():
                run_hash = run_metrics_col.run.hash
                break
        run = aim.Run(run_hash=run_hash, repo=repo, read_only=read_only)
        if run_hash is None:
            exp_info = get_exp_info()
            tags = exp_info.get("tags", {})

            run["dvc_stage_hash"] = uid
            run["git_remote"] = pathlib.Path.cwd().as_posix()
            run["zntrack_node"] = f"{self.node.__module__}.{self.node.__class__.__name__}"
            run["dvc_stage_name"] = self.node.name
            # add a tag for the node
            run.add_tag(self.node.__class__.__name__)
            for tag_name, tag_value in tags.items():
                run.add_tag(f"{tag_name}={tag_value}")

        self.aim_run = run
        return run

    def convert_to_dvc_yaml(self):
        return PLUGIN_EMPTY_RETRUN_VALUE

    def convert_to_params_yaml(self):
        return PLUGIN_EMPTY_RETRUN_VALUE

    def convert_to_zntrack_json(self, graph):
        exp_info = get_exp_info()
        if len(graph.tags) > 0:
            exp_info["tags"] = graph.tags
            set_exp_info(exp_info)

        return PLUGIN_EMPTY_RETRUN_VALUE

    def extend_plots(self, attribute: str, data: dict, reference):
        step = len(reference)
        run = self.get_aim_run()
        for key, value in data.items():
            run.track(value, name=f"{attribute}.{key}", step=step)

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
        try:
            remote_url = repo.remote().url
        except ValueError:
            # ValueError: Remote named 'origin' didn't exist
            remote_url = None

        node_names = []
        with dvc.repo.Repo(rev=rev) as repo:
            for stage in repo.index.stages:
                with contextlib.suppress(AttributeError):
                    # only PipelineStages have a name attribute
                    # we do not need e.g. data stages
                    node_names.append(stage.name)
        for node_name in node_names:
            node = zntrack.from_rev(node_name, rev=rev)
            plugin = cls(node)
            run = plugin.get_aim_run()
            run["git_commit_hash"] = commit_hash
            run["git_commit_message"] = commit_message.strip()
            if remote_url is not None:
                run["git_remote"] = remote_url
            run.experiment = commit_hash
            # raise ValueError(f"Updating {node.name} commit hash to {commit_hash}")
            # what if the experiment is already set?
            # update or keep?
