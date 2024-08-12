import pathlib

DVC_FILE_PATH = pathlib.Path("dvc.yaml")
PARAMS_FILE_PATH = pathlib.Path("params.yaml")
ZNTRACK_FILE_PATH = pathlib.Path("zntrack.json")

ZNTRACK_OPTION = "zntrack.option"
ZNTRACK_CACHE = "zntrack.cache"

ZNTRACK_DEFAULT = object()
ZNTRACK_LAZY_VALUE = object()
