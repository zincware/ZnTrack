from pytrack import PyTrack
from .Example01 import TextToFile


class ProcessData(PyTrack):
    def __init__(self, id_=None, filter_=None):
        super().__init__(id_, filter_)
        self.post_init(id_, filter_)

    def __call__(self):
        self.dvc.deps = [TextToFile(id_=0).files.json_file]

        self.post_call()

    def run(self):
        self.results = sum(TextToFile(id_=0).results["text"])
