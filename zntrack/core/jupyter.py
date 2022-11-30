"""ZnTrack Jupyer Notebook interface."""
import logging
import pathlib
import re
import subprocess
from functools import lru_cache

from zntrack.utils.config import config

log = logging.getLogger(__name__)


@lru_cache(None)
def log_jupyter_warning():
    """Use lru_cache to only print this once."""
    log.warning(
        "Jupyter support is an experimental feature! Please save your "
        "notebook before running this command!\n"
        "Submit issues to https://github.com/zincware/ZnTrack."
    )


def jupyter_class_to_file(nb_name, module_name):
    """Extract the class definition form an ipynb file."""
    # TODO is it really module_name and not class name?

    log_jupyter_warning()
    log.debug(f"Converting {nb_name} to file {module_name}.py")
    nb_name = pathlib.Path(nb_name)

    subprocess.run(
        ["jupyter", "nbconvert", "--to", "script", nb_name.as_posix()],
        capture_output=config.log_level > logging.INFO,
        check=True,
    )

    reading_class = False
    found_node = False

    imports = ""

    class_definition = ""

    with pathlib.Path(nb_name).with_suffix(".py").open("r") as f:
        for line in f:
            if line.startswith("import") or line.startswith("from"):
                imports += line
            if reading_class:
                if (
                    re.match(r"\S", line)
                    and not line.startswith("#")
                    and not line.startswith("class")
                    and not line.startswith("def")
                    and not line.startswith("@")
                    and not line.startswith(")")
                ):
                    reading_class = False
            if reading_class or line.startswith("class"):
                reading_class = True
                class_definition += line
            if line.startswith("@"):  # handle decorators
                reading_class = True
                class_definition += line
            if line.startswith(f"class {module_name}") or line.startswith(
                f"def {module_name}"
            ):
                found_node = True
            if found_node and not reading_class:
                if re.match(r"#.*zntrack:.*break", line):
                    # stop converting the file after this line if the Node was already
                    #  found
                    break

    src = imports + "\n\n" + class_definition

    src_file = pathlib.Path(config.nb_class_path, module_name).with_suffix(".py")
    config.nb_class_path.mkdir(exist_ok=True, parents=True)

    src_file.write_text(src)

    # Remove converted ipynb file
    nb_name.with_suffix(".py").unlink()
