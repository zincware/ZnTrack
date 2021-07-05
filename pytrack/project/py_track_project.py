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

log = logging.getLogger(__file__)


class PyTrackProject(DVCInterface):
    def __init__(self):
        super().__init__()
        self.name = None

    def queue(self):
        """Add this project to the DVC queue"""
        log.info("Running git add")
        subprocess.check_call(['git', 'add', '.'])
        log.info("Queue DVC stage")
        subprocess.check_call(['dvc', 'exp', 'run', '--name', self.name, '--queue'])

    @staticmethod
    def run_all():
        """Run all queried experiments"""
        log.info("RUN DVC stage")
        subprocess.check_call(['dvc', 'exp', 'run', '--run-all'])
        log.info("Running git add")
        subprocess.check_call(['git', 'add', '.'])

    def run(self):
        """Add this experiment to the queue and run the full queue"""
        self.queue()
        self.run_all()

    def load(self):
        """Load this project"""
        subprocess.check_call(['dvc', 'exp', 'apply', self.name])

    def save(self):
        """Save this project to a branch"""
        subprocess.check_call(['dvc', 'exp', 'branch', self.name, self.name])
