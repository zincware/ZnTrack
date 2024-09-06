import contextlib
import pathlib
from dataclasses import Field
from typing import Any

import dvc.repo
import git
import mlflow

from zntrack.config import PLUGIN_EMPTY_RETRUN_VALUE, ZNTRACK_OPTION, ZnTrackOptionEnum
from zntrack.plugins import ZnTrackPlugin
from zntrack.utils.misc import load_env_vars

# TODO: if this plugin fails, there should only be a warning, not an error
# so that the results are not lost


class MLFlowPlugin(ZnTrackPlugin):
    def gitignore_file(self, path: str) -> bool:
        """Add a path to the .gitignore file if it is not already there."""
        with open(".gitignore", "r") as f:
            for line in f:
                if line.strip() == path:
                    return False
        with open(".gitignore", "a") as f:
            f.write(path + "\n")
        return True

    @contextlib.contextmanager
    def get_mlflow_parent_run(self):
        # Can I get rid of this by using cwd and machine_id?
        self.gitignore_file(".mlflow_parent_run_id")
        if pathlib.Path(".mlflow_parent_run_id").exists():
            parent_run_id = pathlib.Path(".mlflow_parent_run_id").read_text().strip()
            with mlflow.start_run(run_id=parent_run_id):
                yield
        else:
            with mlflow.start_run() as run:
                parent_run_id = run.info.run_id
                mlflow.set_tag("git_remote", pathlib.Path.cwd().as_posix())
                pathlib.Path(".mlflow_parent_run_id").write_text(parent_run_id)
                yield

    @contextlib.contextmanager
    def get_mlflow_child_run(self):
        stage_hash = self.node.state.get_stage_hash()
        runs_df = mlflow.search_runs(
            filter_string=f"tags.dvc_stage_hash = '{self.node.state.get_stage_hash()}'",
        )
        if len(runs_df) == 0:
            with self.get_mlflow_parent_run():
                with mlflow.start_run(nested=True):
                    mlflow.set_tag("dvc_stage_hash", stage_hash)
                    mlflow.set_tag("dvc_stage_name", self.node.name)
                    # TODO: do we want to include the name of the parent run?
                    mlflow.set_tag("mlflow.runName", self.node.name)
                    mlflow.set_tag(
                        "zntrack_node",
                        f"{self.node.__module__}.{self.node.__class__.__name__}",
                    )
                    yield
        else:
            print("found existing run")
            with mlflow.start_run(run_id=runs_df.iloc[0].run_id):
                yield

    def getter(self, field: Field) -> Any:
        return PLUGIN_EMPTY_RETRUN_VALUE

    def save(self, field: Field) -> None:
        with self.get_mlflow_child_run():
            if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.PARAMS:
                mlflow.log_param(field.name, getattr(self.node, field.name))
            if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.METRICS:
                mlflow.log_metric(field.name, getattr(self.node, field.name))

    def convert_to_dvc_yaml(self):
        return PLUGIN_EMPTY_RETRUN_VALUE

    def convert_to_params_yaml(self):
        return PLUGIN_EMPTY_RETRUN_VALUE

    def convert_to_zntrack_json(self):
        return PLUGIN_EMPTY_RETRUN_VALUE

    @classmethod
    def finalize(cls, rev: str | None = None):
        """Example:
        -------
        python -c "from zntrack.plugins.mlflow_plugin import MLFlowPlugin; MLFlowPlugin.finalize()"

        """
        # TODO: with the dependency on the file this does not support revs
        # We could add all dvc_stage_hashes to the tags of the parent run
        # and then find the parent run by querying the tags

        if rev is not None:
            raise NotImplementedError("rev is not supported yet")
        import zntrack

        load_env_vars("")

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
                node_names.append(stage.name)

        for node_name in node_names:
            node = zntrack.from_rev(node_name, rev=rev)
            plugin = cls(node)
            with plugin.get_mlflow_parent_run():
                mlflow.set_tag("git_hash", commit_hash)
                mlflow.set_tag("git_commit_message", commit_message)
                if remote_url is not None:
                    mlflow.set_tag("git_remote", remote_url)
                break

        pathlib.Path(".mlflow_parent_run_id").unlink()
