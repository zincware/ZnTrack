import json
import pathlib

import yaml
import znjson


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
    """
    if mkdir:
        file.parent.mkdir(exist_ok=True, parents=True)

    if file.suffix in [".yaml", ".yml"]:
        file.write_text(yaml.safe_dump(value, indent=4))
    elif file.suffix == ".json":
        file.write_text(json.dumps(value, indent=4, cls=znjson.ZnEncoder))
