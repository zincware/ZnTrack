import json
import logging
import pathlib

import yaml
import znjson

log = logging.getLogger(__name__)


def read_file(file: pathlib.Path) -> dict:
    """Read a json/yaml file without the znjson.Decoder

    Parameters
    ----------
    file: pathlib.Path
        The file to read

    Returns
    -------
    dict:
        Content of the json/yaml file
    """
    if file.suffix in [".yaml", ".yml"]:
        with file.open("r") as f:
            file_content = yaml.safe_load(f)
    elif file.suffix == ".json":
        file_content = json.loads(file.read_text())
    else:
        raise NotImplementedError(f"File with suffix {file.suffix} is not supported")
    return file_content


def write_file(file: pathlib.Path, value: dict, mkdir: bool = True):
    """Save dict to file

    Store dictionary to json or yaml file

    Parameters
    ----------
    file: pathlib.Path
        File to save to
    value: dict
        Any serializable data to save
    mkdir: bool
        Create a parent directory if necessary
    """
    if mkdir:
        file.parent.mkdir(exist_ok=True, parents=True)

    if file.suffix in [".yaml", ".yml"]:
        file.write_text(yaml.safe_dump(value, indent=4))
    elif file.suffix == ".json":
        file.write_text(json.dumps(value, indent=4, cls=znjson.ZnEncoder))


def update_config_file(file: pathlib.Path, node_name: str, value_name: str, value):
    """Update a configuration file

    The file structure for node_name is not None is something like
    >>> {node_name: {value_name: value}}
    and for node_name is None:
    >>> {value_name: value}

    Parameters
    ----------
    file: pathlib.Path
        The file to save to
    node_name: str
        the node_name, if None the file is assumed to be {value_name: value}
    value_name: str
        the key of the value to update
    value:
        The value to write to the file
    """
    # Read file
    try:
        file_content = read_file(file)
    except FileNotFoundError:
        file_content = {}
    log.debug(f"Loading <{file}> content: {file_content}")
    if node_name is not None:
        # select primary node name key
        node_content = file_content.get(node_name, {})
        log.debug(f"Gathered <{node_name}> content: {node_content}")
        # update with new value
        node_content[value_name] = value
        log.debug(f"Update <{value_name}> with: {value}")
        # save to file
        file_content[node_name] = node_content
    else:
        log.debug(f"Update <{value_name}> with: {value}")
        file_content[value_name] = value
    write_file(file, value=file_content)
    log.debug(f"Update <{file}> with: {file_content}")
