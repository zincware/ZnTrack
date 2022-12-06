"""Node parameter."""
from __future__ import annotations

import copy
import logging
import pathlib
import typing

import zninit

from zntrack import utils

log = logging.getLogger(__name__)


def uses_node_name(zn_type, instance) -> typing.Union[str, None]:
    """Check if the given metadata is associated with using the node_name as dict key.

    Everything in nodes/<node_name>/ does not need it as key, because the directory
    is already named after the node. On the other side, parameters for example
    require the usage of node_name as a key inside the params.yaml file.

    Parameters
    ----------
    zn_type: utils.ZnTypes
        The Type to look for
    instance:
        Any instance object with the node_name attribute

    Returns
    -------
    str
        returns the node_name if it is being used, otherwise returns None

    """
    if zn_type in utils.VALUE_DVC_TRACKED:
        return None
    return instance.node_name


class ZnTrackOption(zninit.Descriptor):
    """Descriptor for all DVC options.

    This class handles the __get__ and __set__ for the DVC options.
    For most cases this means storing them in the __init__ and keeping track of,
    which Options are used.
    This is required to allow for load=True which updates all ZnTrackOptions,
    based on the computed or otherwise stored values.

    Attributes
    ----------
    file: str
        Either the zntrack file or the parameter file
    dvc_option: str|utils.DVCOptions
        The cmd to use with DVC, e.g. dvc --outs ... would be "outs"
    zn_type: utils.ZnTypes
        The internal ZnType to select the correct ZnTrack behaviour
    allow_lazy: bool, default=True
        Allow this option to be lazy loaded.
    """

    file = None
    dvc_option: str = None
    zn_type: utils.ZnTypes = None
    allow_lazy: bool = True

    def __init__(self, default=zninit.descriptor.Empty, **kwargs):
        """Constructor for ZnTrackOptions.

        Attributes
        ----------
        default: Any
            The default value of the descriptor
        filename:
            part of the kwargs, optional filename overwrite.

        Raises
        ------
        ValueError: If dvc_option is None and the class name is not in utils.DVCOptions

        """
        if (
            default is not zninit.descriptor.Empty
            and self.zn_type in utils.VALUE_DVC_TRACKED
        ):
            raise ValueError(f"Can not set default to a tracked value ({self.zn_type})")
        if self.dvc_option is None:
            # use the name of the class as DVCOption if registered in DVCOptions
            self.dvc_option = utils.DVCOptions(self.__class__.__name__).value

        self.filename = kwargs.pop("filename", self.dvc_option)
        super().__init__(default=default, **kwargs)

    @property
    def dvc_args(self) -> str:
        """replace python variables '_' with '-' for dvc."""
        return self.dvc_option.replace("_", "-")

    def post_dvc_cmd(self, instance) -> typing.List[str]:
        """Optional DVC cmd to run at the end.

        Returns
        -------
        cmd: list[str]
            Get a list for subprocess call to run after the main dvc cmd was executed.
            E.g. ["plots", "modify", ...]
        """
        return None

    def __repr__(self) -> str:
        """Node __repr__."""
        return f"{self.__class__}({hex(id(self))}) for <{self.dvc_option}>"

    def __str__(self) -> str:
        """Node __str__."""
        return f"{self.dvc_option} / {self.name}"

    def _write_instance_dict(self, instance):
        """Write the requested value to instance.__dict__.

        Parameters
        ----------
        instance:
            The instance to be updated

        Returns
        -------
        instance.__dict__ now contains the respective value
        """
        is_lazy_option = instance.__dict__.get(self.name) is utils.LazyOption
        is_not_in_dict = self.name not in instance.__dict__

        if instance.is_loaded and (is_lazy_option or is_not_in_dict):
            # the __dict__ only needs to be updated if __dict__ does
            # not contain self.name or self.name is LazyOption
            try:
                # load data and store it in the instance
                instance.__dict__[self.name] = self.get_data_from_files(instance)
                log.debug(f"instance {instance} updated from file")
            except (KeyError, FileNotFoundError, AttributeError) as err:
                # do not load default value, because a loaded instance should always
                #  load from files.
                if not utils.config.allow_empty_loading:
                    # allow overwriting this
                    raise AttributeError(
                        f"Could not load {self.name} for {instance}"
                    ) from err
        elif is_not_in_dict:
            if self.zn_type in utils.VALUE_DVC_TRACKED:
                raise utils.exceptions.DataNotAvailableError(
                    "Can not access class attributes for a Node which is not loaded."
                    f" Consider using '<Node>.load(name='{instance.node_name}')' to load"
                    " the results"
                )
            # if the instance is not loaded, there is no LazyOption handling
            # instead of .get(name, default_value) we make a copy of the default value
            # because it could be changed.
            instance.__dict__[self.name] = copy.deepcopy(self.default)

    def __get__(self, instance, owner=None, serialize=False):
        """__get__ method.

        Parameters
        ----------
        instance: obj
            The instance to get the attribute from.
        owner: None
            ...
        serialize: bool, default = False.
            return the value to be serialized.
            E.g., if True '$nwd$' will not be converted.
        """
        self._instance = instance

        if instance is None:
            return self
        else:
            self._write_instance_dict(instance)
        return instance.__dict__[self.name]

    def get_filename(self, instance) -> pathlib.Path:
        """Get the name of the file this ZnTrackOption will save its values to."""
        if uses_node_name(self.zn_type, instance) is None:
            return instance.nwd / f"{self.filename}.json"
        return pathlib.Path(self.file)

    def save(self, instance):
        """Save this descriptor for the given instance to file.

        Parameters
        ----------
        instance: Node
            instance where the Descriptor is attached to.
            Similar to __get__(instance) this requires the instance
            to be passed manually.
        """
        if instance.__dict__.get(self.name) is utils.LazyOption:
            # do not save anything if __get__/__set__ was never used
            return
        utils.file_io.update_config_file(
            file=self.get_filename(instance),
            node_name=uses_node_name(self.zn_type, instance),
            value_name=self.name,
            value=self.__get__(instance, self.owner, serialize=True),
        )

    def mkdir(self, instance):
        """Create a parent directory.

        For parameters that are saved in e.g. nodes/<node_name>/file.json
        the nodes/<node_name>/ directory is created here. This is required
        for DVC to create a .gitignore file in these directories.
        """
        file = self.get_filename(instance)
        file.parent.mkdir(exist_ok=True, parents=True)

    def _get_loading_errors(
        self, instance
    ) -> typing.Union[
        utils.exceptions.DataNotAvailableError, utils.exceptions.GraphNotAvailableError
    ]:
        """Raise specific errors when reading ZnTrackOptions.

        Raises
        ------
        DataNotAvailableError:
            if the graph exists in dvc.yaml but the output files do not exist.
        GraphNotAvailableError:
            if the graph does not exist in dvc.yaml. This has higher priority
        """
        if instance._graph_entry_exists:
            return utils.exceptions.DataNotAvailableError(
                f"Could not load data for '{self.name}' from file."
            )
        return utils.exceptions.GraphNotAvailableError(
            f"Could not find the graph configuration for '{instance.node_name}' in"
            f" {utils.Files.dvc}."
        )

    def get_data_from_files(self, instance):
        """Load the value/s for the given instance from the file/s.

        Parameters
        ----------
        instance: Node
            instance where the Descriptor is attached to.
            Similar to __get__(instance) this requires the instance
            to be passed manually.

        Returns
        -------
        any:
            returns the value loaded from file/s for the given instance.
        """
        file = self.get_filename(instance)
        try:
            file_content = utils.file_io.read_file(file)
        except FileNotFoundError as err:
            raise self._get_loading_errors(instance) from err
        # The problem here is, that I can not / don't want to load all Nodes but
        # only the ones, that are in [self.node_name][self.name] for deserializing
        try:
            if uses_node_name(self.zn_type, instance) is not None:
                values = utils.decode_dict(file_content[instance.node_name][self.name])
            else:
                values = utils.decode_dict(file_content[self.name])
        except KeyError as err:
            raise self._get_loading_errors(instance) from err
        log.debug(f"Loading {instance.node_name} from {file}: ({values})")
        return values
