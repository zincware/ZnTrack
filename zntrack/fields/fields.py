"""Fields that are used to define Nodes."""

from zntrack.fields.dependency import Dependency
from zntrack.fields.dvc.options import DVCOption, PlotsOption
from zntrack.fields.zn.options import Output, Params, Plots

# Serialized Fields


def outs():
    """Define a Node Output.

    Parameters
    ----------
        data: any
            A data object that is generated by the Node.
            The object is serialized and deserialized by ZnTrack
            and stored in the node working directory.
            see https://dvc.org/doc/command-reference/stage/add#-o
    """
    return Output(dvc_option="outs", use_repr=False)


def metrics():
    """Define a Node Metric.

    Parameters
    ----------
        data: dict
            A dictionary that is used by DVC as a metric.
            The object is serialized and deserialized by ZnTrack
            and stored in the node working directory.
            see https://dvc.org/doc/command-reference/stage/add#-M

    """
    return Output(dvc_option="metrics-no-cache")


def params(*args, **kwargs):
    """Define a Node Parameter.

    Parameters
    ----------
    args: any
        A data object that is used as a parameter.
        Typically, this should be a string or number.
        The object is serialized and deserialized by ZnTrack
        and stored in params.yaml.
        see https://dvc.org/doc/command-reference/stage/add#-p
    kwargs: dict
        Additional keyword arguments.
    """
    return Params(*args, **kwargs)


def deps(*data):
    """Define a Node Dependency.

    Parameters
    ----------
    data: any
        A data object that is used as a dependency.
        This can either be a Node or an attribute of a Node.
        It can not be an object that is not part of the Node graph.
        see https://dvc.org/doc/command-reference/stage/add#-d
    """
    return Dependency(*data)


def plots(*args, **kwargs):
    """Define a Node Plot.

    Parameters
    ----------
    args: pd.DataFrame
        A pandas DataFrame that is used as a plot.
        The object is serialized and deserialized by ZnTrack
        and stored in the node working directory.
        see https://dvc.org/doc/command-reference/stage/add#--plots
    kwargs: dict
        Additional keyword arguments that are used for plotting.

    """
    return Plots(*args, **kwargs)


# Path Fields


def outs_path(*args, dvc_option="outs", **kwargs):
    """Define a Node Output.

    Parameters
    ----------
    args: str|Path
        A file or directory that is generated by the Node.
        see https://dvc.org/doc/command-reference/stage/add#-o
    dvc_option: str, default="outs"
        The DVC option to use for this field.
    kwargs: dict
        Additional keyword arguments.

    """
    return DVCOption(*args, dvc_option=dvc_option, **kwargs)


def metrics_path(*args, dvc_option="metrics", **kwargs):
    """Define a Node Metric.

    Parameters
    ----------
    args : str|Path
        A file that is used by DVC as a metric, such as *.json
        see https://dvc.org/doc/command-reference/stage/add#-M
    dvc_option: str, default="metrics"
        The DVC option to use for this field.
    kwargs: dict
        Additional keyword arguments.

    """
    return DVCOption(*args, dvc_option=dvc_option, **kwargs)


def params_path(*args, **kwargs):
    """Define a Node Parameter.

    Parameters
    ----------
    args : str|Path
        A file that is used by DVC for reading parameters.
        This includes typically json or yaml files.
        see https://dvc.org/doc/command-reference/stage/add#-p
    kwargs: dict
        Additional keyword arguments.
    """
    return DVCOption(*args, dvc_option="params", **kwargs)


def deps_path(*args, **kwargs):
    """Define a Node Dependency.

    Parameters
    ----------
    args : str|Path
        A file or directory that is defined as a dependency to the Node.
        see https://dvc.org/doc/command-reference/stage/add#-d
    kwargs: dict
        Additional keyword arguments.

    """
    return DVCOption(*args, dvc_option="deps", **kwargs)


def plots_path(*args, dvc_option="plots", **kwargs):
    """Define a Node Plot.

    Parameters
    ----------
    args : str|Path
        A file or directory that is defined as a plot to the Node.
        see https://dvc.org/doc/command-reference/stage/add#--plots
    dvc_option: str, default="plots"
        The DVC option to use for this field.
    kwargs: dict
        Additional keyword arguments that are used for plotting.
    """
    return PlotsOption(*args, dvc_option=dvc_option, **kwargs)
