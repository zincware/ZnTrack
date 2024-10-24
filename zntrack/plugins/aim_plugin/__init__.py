import contextlib
import dataclasses
import os
import pathlib
import typing as t
import uuid

import aim
import dvc.repo
import git
import pandas as pd
import znflow

from zntrack.config import PLUGIN_EMPTY_RETRUN_VALUE, ZNTRACK_OPTION, ZnTrackOptionEnum
from zntrack.node import Node
from zntrack.plugins import ZnTrackPlugin, get_exp_info, set_exp_info
from zntrack.utils import module_handler
from zntrack.utils.misc import load_env_vars

if t.TYPE_CHECKING:
    pass


def _create_aim_run(
    aim_repo, experiment, stage_hash, stage_name, node_path, tags: dict[str, str]
) -> str:
    assert experiment.startswith("exp-")
    run = aim.Run(repo=aim_repo, experiment=experiment)
    run["dvc_stage_hash"] = stage_hash
    run["dvc_stage_name"] = stage_name
    run["zntrack_node"] = node_path
    for tag_key, tag_value in tags.items():
        run.add_tag(f"{tag_key}={tag_value}")
    run.close()
    return run.hash


def get_original_run_data(stage_hash: str) -> pd.DataFrame:
    """Retrieve parameters from the original run."""
    load_env_vars()
    aim_repo = aim.Repo(path=os.environ["AIM_TRACKING_URI"])
    for run_metrics_col in aim_repo.query_metrics(
        f"run.dvc_stage_hash == '{stage_hash}'"
    ).iter():
        return run_metrics_col.run.dataframe()
    raise ValueError(f"Unable to find run with dvc_stage_hash {stage_hash}")


def get_aim_run_id(stage_hash: str, stage_name: str, node_path: str) -> tuple[str, bool]:
    load_env_vars()
    aim_repo = aim.Repo(path=os.environ["AIM_TRACKING_URI"])
    exp_info = get_exp_info()
    experiment = exp_info.get("aim_experiment")
    tags = exp_info.get("tags", {})
    if experiment is None:
        experiment = f"exp-{uuid.uuid4().hex[:8]}"
        exp_info["aim_experiment"] = experiment
        set_exp_info(exp_info)
        return (
            _create_aim_run(
                aim_repo, experiment, stage_hash, stage_name, node_path, tags
            ),
            True,
        )
    else:
        for run_metrics_col in aim_repo.query_metrics(
            f"run.dvc_stage_hash == '{stage_hash}' and run.experiment == '{experiment}'"
        ).iter():
            return run_metrics_col.run.hash, False
        return (
            _create_aim_run(
                aim_repo, experiment, stage_hash, stage_name, node_path, tags
            ),
            True,
        )


class AIMPlugin(ZnTrackPlugin):
    """ZnTrack integration with AIM.

    ```mermaid
    flowchart LR
        repo --> commit --> stage

        subgraph AIM repo
        repo
        end
        subgraph Experiment
        commit
        end
        subgraph Run
        stage
        end
    ```
    """

    _continue_on_error_ = True

    def setup(self):
        self.run = None
        self.run_id, self.new_run = get_aim_run_id(
            self.node.state.get_stage_hash(),
            self.node.name,
            f"{self.node.__module__}.{self.node.__class__.__name__}",
        )

    def getter(self, field: dataclasses.Field) -> t.Any:
        # The AIM plugin relies on others, e.g. DVCPlugin for loading/saving data
        return PLUGIN_EMPTY_RETRUN_VALUE

    def save(self, field: dataclasses.Field) -> None:
        if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.PARAMS:
            with self.get_aim_run() as run:
                run[field.name] = getattr(self.node, field.name)
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
            with self.get_aim_run() as run:
                run[field.name] = (
                    new_content
                    if isinstance(getattr(self.node, field.name), list)
                    else new_content[0]
                )
        if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.METRICS:
            with self.get_aim_run() as run:
                assert isinstance(getattr(self.node, field.name), dict)

                for key, value in getattr(self.node, field.name).items():
                    run.track(value, name=f"{field.name}.{key}")

        if field.metadata.get(ZNTRACK_OPTION) == ZnTrackOptionEnum.PLOTS:
            df: pd.DataFrame = getattr(self.node, field.name).copy()
            with self.get_aim_run() as run:
                for idx, row in df.iterrows():
                    for key, value in row.items():
                        run.track(value, name=f"{field.name}.{key}", step=idx)

    @contextlib.contextmanager
    def get_aim_run(self) -> t.Iterator[aim.Run]:
        if not hasattr(self, "run_id") or self.run_id is None:
            self.setup()
        exp_info = get_exp_info()
        experiment = exp_info.get("aim_experiment")
        run = aim.Run(
            run_hash=self.run_id,
            repo=aim.Repo(path=os.environ["AIM_TRACKING_URI"]),
            experiment=experiment,
        )
        yield run
        run.close()

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
    def finalize(cls, **kwargs) -> None:
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
        load_env_vars()

        exp_info = get_exp_info()
        if "aim_experiment" not in exp_info:
            raise ValueError("Unable to find an AIM experiment.")

        import zntrack

        tags = exp_info.get("tags", {})

        repo = git.Repo(".")
        if repo.is_dirty():
            raise ValueError("Can only finalize a clean git repository")

        commit_hash = repo.head.commit.hexsha
        commit_message = repo.head.commit.message

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
            # TODO: this will create all nodes, even those, that were cached.
            # currently, they are missing parameters and original_run_id
            # but they will have the dvc_stage_hash
            # should be original_dvc_stage_hash and original_run_id instead.
            # and the parameters should be filled in from the original run

            node = zntrack.from_rev(node_name)
            plugin = cls(node)

            with plugin.get_aim_run() as run:
                if plugin.new_run:
                    # move dvc_stage_hash to original_dvc_stage_hash
                    run["original_dvc_stage_hash"] = run["dvc_stage_hash"]
                    del run["dvc_stage_hash"]
                    original_run_df = get_original_run_data(node.state.get_stage_hash())
                    run_df = run.dataframe()
                    for key, value in original_run_df.items():
                        if key in ["dvc_stage_name", "dvc_stage_hash", "zntrack_node"]:
                            continue
                        if key not in run_df.columns:
                            run[key] = value[0]
                    run["original_run_id"] = original_run_df["hash"][0]
                run["git_commit_hash"] = commit_hash
                run["git_commit_message"] = commit_message.strip()
                if remote_url is not None:
                    run["git_remote"] = remote_url

        exp_info.pop("aim_experiment")
        set_exp_info(exp_info)

        # import zntrack

        # repo = git.Repo(".")

        # if rev is None:
        #     commit_hash = repo.head.commit.hexsha
        #     commit_message = repo.head.commit.message
        # else:
        #     commit_hash = repo.commit(rev).hexsha
        #     commit_message = repo.commit(rev).message

        # # get the default remote for the current branch
        # try:
        #     remote_url = repo.remote().url
        # except ValueError:
        #     # ValueError: Remote named 'origin' didn't exist
        #     remote_url = None

        # node_names = []
        # with dvc.repo.Repo(rev=rev) as repo:
        #     for stage in repo.index.stages:
        #         with contextlib.suppress(AttributeError):
        #             # only PipelineStages have a name attribute
        #             # we do not need e.g. data stages
        #             node_names.append(stage.name)
        # for node_name in node_names:
        #     node = zntrack.from_rev(node_name, rev=rev)
        #     plugin = cls(node)
        #     with plugin.get_aim_run() as run:
        #         run["git_commit_hash"] = commit_hash
        #         run["git_commit_message"] = commit_message.strip()
        #         if remote_url is not None:
        #             run["git_remote"] = remote_url
        #         run.experiment = commit_hash
        #     # raise ValueError(f"Updating {node.name} commit hash to {commit_hash}")
        #     # what if the experiment is already set?
        #     # update or keep?

        # # TODO: remove exp key from exp_info
