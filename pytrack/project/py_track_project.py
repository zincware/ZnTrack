"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: The class for the PyTrackProject
"""
import logging

from pytrack.interface import DVCInterface
import subprocess
from datetime import datetime

log = logging.getLogger(__file__)


class PyTrackProject(DVCInterface):
    """PyTrack Project to handle experiments via subprocess calls to DVC"""

    def __init__(self, name: str = None):
        """

        Parameters
        ----------
        name: str (optional)
            Name of the project
        """
        super().__init__()
        if name is None:
            name = f'PyTrackProject_{datetime.now().strftime("%Y_%m_%d-%H_%M_%S")}'
        self.name = name

    def queue(self, name: str = None):
        """Add this project to the DVC queue"""
        if name is not None:
            self.name = name
        log.info("Running git add")
        subprocess.check_call(["git", "add", "."])
        log.info("Queue DVC stage")
        subprocess.check_call(["dvc", "exp", "run", "--name", self.name, "--queue"])

    @staticmethod
    def remove_queue():
        """Empty the queue"""
        log.warning("Removing all queried experiments!")
        subprocess.check_call(["dvc", "exp", "remove", "--queue"])

    @staticmethod
    def run_all():
        """Run all queried experiments"""
        log.info("RUN DVC stage")
        subprocess.check_call(["dvc", "exp", "run", "--run-all"])
        log.info("Running git add")
        subprocess.check_call(["git", "add", "."])

    def run(self, name: str = None):
        """Add this experiment to the queue and run the full queue"""
        self.queue(name=name)
        self.run_all()
        log.info("Finished")

    def load(self, name=None):
        """Load this project"""
        if name is not None:
            self.name = name
        subprocess.check_call(["dvc", "exp", "apply", self.name])

    def save(self):
        """Save this project to a branch"""
        subprocess.check_call(["dvc", "exp", "branch", self.name, self.name])

    def create_dvc_repository(self):
        """Perform git and dvc init"""
        try:
            subprocess.check_call(["dvc", "status"])
            log.info("DVC Repository already exists.")
        except subprocess.CalledProcessError:
            subprocess.check_call(["git", "init"])
            subprocess.check_call(["dvc", "init"])
            subprocess.check_call(["git", "add", "."])
            subprocess.check_call(["git", "commit", "-m", f"Initialize {self.name}"])

    @staticmethod
    def _destroy():
        subprocess.check_call(["dvc", "destroy", "-f"])
