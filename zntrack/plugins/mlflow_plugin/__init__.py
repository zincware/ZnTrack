import contextlib
import pathlib
import warnings
from dataclasses import Field, dataclass
from typing import Any

import dvc.repo
import git
import mlflow
from mlflow.utils import mlflow_tags

from zntrack.config import PLUGIN_EMPTY_RETRUN_VALUE, ZNTRACK_OPTION, ZnTrackOptionEnum
from zntrack.plugins import ZnTrackPlugin
from zntrack.utils.misc import load_env_vars

# TODO: if this plugin fails, there should only be a warning, not an error
# so that the results are not lost
# TODO: have the mlflow run active over the entire run method to avoid searching for it over again.
# TODO: in finalize have the parent run active (if not already)


@dataclass
class MLFlowPlugin(ZnTrackPlugin):
    def __post_init__(self):
        load_env_vars("")

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

    def get_run_info(self) -> dict:
        with self.get_mlflow_child_run():
            # get the name of the current run
            run_info = mlflow.active_run().info
            experiment_id = run_info.experiment_id
            # run_name = run_info.run_name
            try:
                run_name = mlflow.get_run(run_info.run_id).data.tags[
                    mlflow_tags.MLFLOW_RUN_NAME
                ]
            except KeyError:
                run_name = run_info.run_name
            run_id = run_info.run_id
            host_url = mlflow.get_tracking_uri()
            uri = f"{host_url}/#/experiments/{experiment_id}/runs/{run_id}"
            return {"name": run_name, "uri": uri, "id": run_id}

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
                    mlflow.set_tag(mlflow_tags.MLFLOW_RUN_NAME, self.node.name)
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
                metrics = getattr(self.node, field.name)
                for key, value in metrics.items():
                    mlflow.log_metric(f"{field.name}.{key}", value)
                    # TODO: plots
                    # TODO: define tags for all experiments in a parent run

    def convert_to_dvc_yaml(self):
        return PLUGIN_EMPTY_RETRUN_VALUE

    def convert_to_params_yaml(self):
        return PLUGIN_EMPTY_RETRUN_VALUE

    def convert_to_zntrack_json(self):
        return PLUGIN_EMPTY_RETRUN_VALUE

    def extend_plots(self, attribute: str, data: dict, reference):
        step = len(reference)
        new_data = {f"{attribute}.{key}": value for key, value in data.items()}
        with self.get_mlflow_child_run():
            mlflow.log_metrics(new_data, step=step)

    @classmethod
    def finalize(cls, rev: str | None = None):
        """Example:
        -------
        python -c "from zntrack.plugins.mlflow_plugin import MLFlowPlugin; MLFlowPlugin.finalize()"

        """
        # TODO: with the dependency on the file this does not support revs
        # We could add all dvc_stage_hashes to the tags of the parent run
        # and then find the parent run by querying the tags

        # TODO: provide post-commit installation instructions

        if rev is not None:
            raise NotImplementedError("rev is not supported yet")
        load_env_vars("")

        if not pathlib.Path(".mlflow_parent_run_id").exists():
            raise ValueError("Unable to find '.mlflow_parent_run_id' file")
        import zntrack

        repo = git.Repo(".")
        if repo.is_dirty():
            raise ValueError("Can only finalize a clean git repository")

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
                    #  we do not need data stages
                    node_names.append(stage.name)

        for node_name in node_names:
            node = zntrack.from_rev(node_name, rev=rev)
            plugin = cls(node)

            with plugin.get_mlflow_parent_run():
                mlflow.set_tag("git_hash", commit_hash)
                mlflow.set_tag("git_commit_message", commit_message)
                if remote_url is not None:
                    mlflow.set_tag("git_remote", remote_url)
                parent_run_id = mlflow.active_run().info.run_id
                active_experiment_id = mlflow.active_run().info.experiment_id
            break

        child_runs = mlflow.search_runs(
            experiment_ids=[active_experiment_id],
            filter_string=f"tags.{mlflow_tags.MLFLOW_PARENT_RUN_ID} = '{parent_run_id}'",
        )
        print(f"found {len(child_runs)} child runs in exp: '{active_experiment_id}'")
        for node_name in node_names:
            if node_name in child_runs["tags.dvc_stage_name"].values:
                node = zntrack.from_rev(node_name, rev=rev)
                with node.state.plugins["MLFlowPlugin"].get_mlflow_child_run():
                    mlflow.set_tag("git_hash", commit_hash)
                    mlflow.set_tag("git_commit_message", commit_message)
                    if remote_url is not None:
                        mlflow.set_tag("git_remote", remote_url)
            else:
                print(f"missing {node_name}")
                node = zntrack.from_rev(node_name, rev=rev)
                stage_hash = node.state.get_stage_hash()
                original_runs = mlflow.search_runs(
                    experiment_ids=[active_experiment_id],
                    filter_string=f"tags.dvc_stage_hash = '{stage_hash}'",
                )
                print(f"searching for original run {stage_hash=}")
                if len(original_runs) == 0:
                    warnings.warn(f"no original run found for {node_name} - skipping")
                    continue
                if len(original_runs) > 1:
                    warnings.warn(
                        f"multiple original runs found for {node_name} - skipping"
                    )
                    continue
                print(f"found original run for {node_name} - {original_runs}")
                original_run_id = original_runs.iloc[0].run_id
                with cls(node).get_mlflow_parent_run():
                    with mlflow.start_run(nested=True):
                        mlflow.set_tag("dvc_stage_name", node.name)
                        mlflow.set_tag(
                            "zntrack_node",
                            f"{node.__module__}.{node.__class__.__name__}",
                        )
                        mlflow.set_tag("original_run_id", original_run_id)
                        # copy parameters and metrics from the original run
                        original_run = mlflow.get_run(original_run_id)
                        for key, value in original_run.data.params.items():
                            mlflow.log_param(key, value)
                        for key, value in original_run.data.metrics.items():
                            mlflow.log_metric(key, value)

                        # set git hash and commit message
                        mlflow.set_tag("git_hash", commit_hash)
                        mlflow.set_tag("git_commit_message", commit_message)
                        if remote_url is not None:
                            mlflow.set_tag("git_remote", remote_url)

                        mlflow.set_tag(
                            "original_dvc_stage_hash", node.state.get_stage_hash()
                        )
                        mlflow.set_tag(mlflow_tags.MLFLOW_RUN_NAME, node_name)
        pathlib.Path(".mlflow_parent_run_id").unlink()
