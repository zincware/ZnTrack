import zntrack
import typing as t

class MyNode(zntrack.Node):
    deps_path: t.Union[list[t.Union[str, None]], None] = zntrack.deps_path()
    params_path: t.Union[list[t.Union[str, None]], None] = zntrack.params_path()
    outs_path: t.Union[list[t.Union[str, None]], None] = zntrack.outs_path()
    metrics_path: t.Union[list[t.Union[str, None]], None] = zntrack.metrics_path()
    plots_path: t.Union[list[t.Union[str, None]], None] = zntrack.plots_path()

    def run(self):
        pass

def test_x_path_none():
    project = zntrack.Project()

    with project:
        node_none = MyNode(
            deps_path=None,
            params_path=None,
            outs_path=None,
            metrics_path=None,
            plots_path=None,
        )
        # node_list_none = MyNode(
        #     deps_path=[None],
        #     params_path=[None],
        #     outs_path=[None],
        #     metrics_path=[None],
        #     plots_path=[None],
        # )

    project.build()
