import sys
import logging

from dvc_op import DVCOp
from dvc_op.core.dataclasses import DVCParams

import numpy as np
import ase.io
import ase.db
from tqdm import tqdm

from pathlib import Path

log = logging.getLogger(__file__)


def numbers_to_keys(atomic_numbers) -> dict:
    """Convert atomic numbers from ase to atomic keys for TFDescriptors

    Returns
    -------
    dict: converted from np.int32 to int
    """
    out = dict(zip(*np.unique(atomic_numbers, return_counts=True)))

    return {int(key): int(val) for key, val in out.items()}


class AddData(DVCOp):
    """Demo function that could represent data loading"""

    def __init__(self):
        """
        The Init function does not take any arguments!
        """
        super().__init__()
        self.dvc = DVCParams(
            multi_use=True,
            outs=['database.db']
        )

    def __call__(self, path, name=None, comment="", exec_: bool = False, slurm: bool = False, force: bool = False):
        """User interface

        Parameters
        ----------
        path: str, Path
            Path to the file to be added to the database
        name: str, None
            Unique name to identify the database. If None, it tries to use the filename.
        comment: str, optional
            Some comment
        exec_: bool, False
            Run the stage directly. On default it'll be staged but not executed.
        slurm: bool, default = False
            Use SRUN and self.slurm_config to run this command on a SLURM Cluster
        """
        if isinstance(path, Path):
            path = str(path)

        if name is None:
            name = Path(path).stem

        self.parameters = dict(name=name, path=path, comment=comment)
        self.post_call(exec_=exec_, slurm=slurm, force=force)

    def run_dvc(self, id_=0):
        """DVC Interface

        DVC will run this function to perform the actual computation

        Parameters
        ----------
        id_: int
            For multi_use this number represents the stage identifier
        """
        self.pre_run(id_)

        mean_energy = []

        data_read = ase.io.read(self.parameters['path'], index=":")
        with ase.db.connect(self.files.outs[0]) as database:
            for ase_atoms in tqdm(data_read, ncols=100, file=sys.stdout):
                mean_energy.append(ase_atoms.get_potential_energy())
                database.write(ase_atoms, group=self.parameters['name'])

        # ase_atoms: Atoms
        cell = ase_atoms.get_cell().tolist()
        # atomic_numbers = [int(x) for x in ase_atoms.get_atomic_numbers()]  # convert np.int32 -> int32
        atomic_keys = numbers_to_keys(ase_atoms.get_atomic_numbers())

        database_groups = self.parameters
        database_groups.update(dict(
            id_=self.id,
            len=len(data_read),
            cell=cell,
            atomic_keys=atomic_keys,
            mean_energy=np.mean(mean_energy)
        ))

        self.results = database_groups

    def load_full_database(self, property_: str = None) -> list:
        """Query the full ASE database

        Parameters
        ---------
        property_: str
            A name, e.g. "energy" that can directly be accessed from the database object and be returned instead
            of a list of Atoms.

        Useful e.g. for Clustering methods
        """
        atoms = []
        log.debug("Start querying database")
        with ase.db.connect(self.files.outs[0]) as db:
            for row in db.select():
                if property_ is None:
                    atoms.append(row.toatoms())
                elif property_ == "energy":
                    atoms.append(row.toatoms().get_potential_energy())
        log.debug("Finished querying database")

        if property_ == "energy":
            atoms = np.array(atoms)

        return atoms

    def load_database_generator(self, configuration_ids: list, database_id: int):
        """Generator to load data from the database

        Parameters
        ----------
        configuration_ids: list
            List of integer atoms ids that shall be queried from the database
        database_id: int
            ID of the database

        Returns
        -------

        Atoms: generates the ASE Atoms objects

        """
        with ase.db.connect(self.data_path['outputs'] / self.convert_outs(self.outputs[0], id_=database_id)) as db:
            for configuration_id in configuration_ids:
                yield db.get_atoms(int(configuration_id))

    def load_database(self, configuration_ids: dict) -> dict:
        """

        Parameters
        ----------
        configuration_ids: dict
            Dictionary of the type {id: [ids]}

        Returns
        -------
        dict: Dictionary of ASE objects ordered by databases, so different cell sizes can be handled differently

        """

        atoms_list = {}
        for database_id, configuration_id in configuration_ids.items():
            atoms_list[database_id] = list(self.load_database_generator(
                configuration_ids=configuration_id, database_id=database_id)
            )

        return atoms_list
