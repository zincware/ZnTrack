import contextlib
import dataclasses
import pathlib
import warnings
from dataclasses import Field, dataclass
from typing import Any

import dvc.repo
import git
import mlflow
import pandas as pd
import yaml
import znflow
from mlflow.utils import mlflow_tags

from zntrack.config import (
    EXP_INFO_PATH,
    PLUGIN_EMPTY_RETRUN_VALUE,
    ZNTRACK_OPTION,
    ZnTrackOptionEnum,
)
from zntrack.node import Node
from zntrack.plugins import ZnTrackPlugin, get_exp_info, set_exp_info
from zntrack.utils import module_handler
from zntrack.utils.misc import load_env_vars

# TODO: if this plugin fails, there should only be a warning, not an error
# so that the results are not lost
# TODO: have the mlflow run active over the entire run method to avoid searching for it over again.
# TODO: in finalize have the parent run active (if not already)


def get_mlflow_parent_run() -> str:
    # Can I get rid of this by using cwd and machine_id?

    exp_info = get_exp_info()
    try:
        parent_run_id = exp_info["parent_run_id"]
        mlflow.start_run(run_id=parent_run_id)
        return parent_run_id

    except KeyError:
        run = mlflow.start_run()
        parent_run_id = run.info.run_id
        exp_info["parent_run_id"] = parent_run_id
        set_exp_info(exp_info)

        # set tags
        tags = exp_info.get("tags", {})
        for tag_key, tag_value in tags.items():
            mlflow.set_tag(tag_key, tag_value)
        return parent_run_id


def get_mlflow_child_run(stage_hash: str, node: Node, node_path: str) -> str:
    runs_df = mlflow.search_runs(
        filter_string=f"tags.dvc_stage_hash = '{stage_hash}'",
    )
    if len(runs_df) == 0:
        # we assume there is an active run, maybe test?
        run = mlflow.start_run(nested=True)
        warnings.warn("Creating new child run")
        exp_info = get_exp_info()
        tags = exp_info.get("tags", {})

        mlflow.set_tag("dvc_stage_hash", stage_hash)
        mlflow.set_tag("dvc_stage_name", node.name)
        # TODO: do we want to include the name of the parent run?
        mlflow.set_tag(mlflow_tags.MLFLOW_RUN_NAME, node.name)
        mlflow.set_tag(
            "zntrack_node",
            node_path,
        )
        for tag_key, tag_value in tags.items():
            mlflow.set_tag(tag_key, tag_value)
        return run.info.run_id
    else:
        print("found existing run")
        run_id = runs_df.iloc[0].run_id
        mlflow.start_run(run_id=run_id, nested=True)
        return run_id


@dataclass
class MLFlowPlugin(ZnTrackPlugin):
    """ZnTrack integration with MLFlow.

    ```mermaid
    flowchart LR
        repo --> commit --> stage

        subgraph Experiment
        repo
        end
        subgraph Parent Run
        commit
        end
        subgraph Child Run
        stage
        end
    ```
    """

    _continue_on_error_ = True
    parent_run_id = None
    child_run_id = None

    def __post_init__(self):
        load_env_vars("")
        # can not load the runs in here, because the node name is not set yet.

    def setup(self):
        # 1. find the parent run, create one if it does not exist
        # 2. find the child run, create one if it does not exist

        self.parent_run_id = self.parent_run_id or get_mlflow_parent_run()
        self.child_run_id = self.child_run_id or get_mlflow_child_run(
            self.node.state.get_stage_hash(),
            self.node,
            f"{self.node.__module__}.{self.node.__class__.__name__}",
        )

    def close(self):
        # close both the parent and the child run
        while mlflow.active_run():
            mlflow.end_run()

    def get_run_info(self) -> dict:
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

    def getter(self, field: Field) -> Any:
        return PLUGIN_EMPTY_RETRUN_VALUE

    def save(self, field: Field) -> None:
        if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.PARAMS:
            mlflow.log_param(field.name, getattr(self.node, field.name))
        if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.DEPS:
            content = getattr(self.node, field.name)
            new_content = []
            if not isinstance(content, (list, tuple)):
                content = [content]
                # TODO: code duplication with the other plugins!
            for val in content:
                if dataclasses.is_dataclass(val) and not isinstance(
                    val, (Node, znflow.Connection, znflow.CombinedConnections)
                ):
                    # We save the values of the passed dataclasses
                    #  to the params.yaml file to be later used
                    #  by the DataclassContainer to recreate the
                    #  instance with the correct parameters.
                    dc_params = dataclasses.asdict(val)
                    dc_params["_cls"] = f"{module_handler(val)}.{val.__class__.__name__}"
                    new_content.append(dc_params)
            mlflow.log_param(field.name, new_content)

        if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.METRICS:
            metrics = getattr(self.node, field.name)
            for key, value in metrics.items():
                mlflow.log_metric(f"{field.name}.{key}", value)
                # TODO: plots
                # TODO: define tags for all experiments in a parent run
        if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.PLOTS:
            df: pd.DataFrame = getattr(self.node, field.name).copy()
            for idx, row in df.iterrows():
                for key, value in row.items():
                    mlflow.log_metric(f"{field.name}.{key}", value, step=idx)

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

    @classmethod
    def finalize(cls, **kwargs):
        """Example:
        -------
        python -c "from zntrack.plugins.mlflow_plugin import MLFlowPlugin; MLFlowPlugin.finalize()"

        """
        # TODO: with the dependency on the file this does not support revs
        # We could add all dvc_stage_hashes to the tags of the parent run
        # and then find the parent run by querying the tags

        # TODO: provide post-commit installation instructions
        # TODO: kwarg for updating cached runs
        load_env_vars()
        skip_cached = kwargs.get("skip_cached", True)
        update_run_names = kwargs.get("update_run_names", True)

        exp_info = get_exp_info()
        if "parent_run_id" not in exp_info:
            raise ValueError("Unable to find parent run id")
        import zntrack

        tags = exp_info.get("tags", {})

        repo = git.Repo(".")
        if repo.is_dirty():
            raise ValueError("Can only finalize a clean git repository")

        commit_hash = repo.head.commit.hexsha
        commit_message = repo.head.commit.message

        prefix = commit_message.split()[0]

        # get the default remote for the current branch
        try:
            remote_url = repo.remote().url
        except ValueError:
            # ValueError: Remote named 'origin' didn't exist
            remote_url = None

        node_names = []
        with dvc.repo.Repo() as repo:
            for stage in repo.index.stages:
                with contextlib.suppress(AttributeError):
                    # only PipelineStages have a name attribute
                    #  we do not need data stages
                    node_names.append(stage.name)

        for node_name in node_names:
            node = zntrack.from_rev(node_name)
            plugin = cls(node)

            with plugin:
                pass  # load run_id states
            with mlflow.start_run(run_id=plugin.parent_run_id):
                mlflow.set_tag("git_commit_hash", commit_hash)
                mlflow.set_tag("git_commit_message", commit_message)
                mlflow.set_tag(mlflow_tags.MLFLOW_RUN_NAME, prefix)
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
                node = zntrack.from_rev(node_name, rev=commit_hash)
                with node.state.plugins["MLFlowPlugin"]:
                    mlflow.set_tag("git_commit_hash", commit_hash)
                    mlflow.set_tag("git_commit_message", commit_message.strip())
                    # mlflow.set_tag(
                    #     mlflow_tags.MLFLOW_RUN_NOTE, f"{commit_message.strip()}"
                    # )
                    # there is https://github.com/mlflow/mlflow/blob/master/tests/tracking/context/test_git_context.py
                    #  but it is not documented?
                    mlflow.set_tag(mlflow_tags.MLFLOW_GIT_COMMIT, commit_hash)
                    if update_run_names:
                        mlflow.set_tag(
                            mlflow_tags.MLFLOW_RUN_NAME, f"{prefix}:{node_name}"
                        )
                    if remote_url is not None:
                        mlflow.set_tag("git_remote", remote_url)
                        mlflow.set_tag(mlflow_tags.MLFLOW_GIT_REPO_URL, remote_url)
                    if hasattr(node, "__run_note__"):
                        mlflow.set_tag(mlflow_tags.MLFLOW_RUN_NOTE, node.__run_note__())
                    # if hasattr(node, "_mlflow_run_note_"):
                    # raise ValueError("not implemented")
            elif not skip_cached:
                print(f"missing {node_name}")
                node = zntrack.from_rev(node_name, rev=commit_hash)
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

                get_mlflow_parent_run()
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
                    mlflow.set_tag("git_commit_hash", commit_hash)
                    mlflow.set_tag("git_commit_message", commit_message.strip())
                    if remote_url is not None:
                        mlflow.set_tag("git_remote", remote_url)

                    mlflow.set_tag("original_dvc_stage_hash", node.state.get_stage_hash())
                    if hasattr(node, "__run_note__"):
                        mlflow.set_tag(mlflow_tags.MLFLOW_RUN_NOTE, node.__run_note__())
                    mlflow.set_tag(mlflow_tags.MLFLOW_RUN_NAME, node_name)
                    for tag_key, tag_value in tags.items():
                        mlflow.set_tag(tag_key, tag_value)
                while mlflow.active_run():
                    mlflow.end_run()

        # remove the parent run id exp_info
        exp_info.pop("parent_run_id")
        set_exp_info(exp_info)
