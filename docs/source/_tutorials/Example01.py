from pytrack import PyTrack


class TextToFile(PyTrack):
    def __init__(self, id_=None, filter_=None):
        super().__init__(id_, filter_)
        self.post_init(id_, filter_)

    def __call__(self, text: str):
        self.parameters = {"text": text}
        self.post_call()

    def run(self):
        self.results = self.parameters
