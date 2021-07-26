from pytrack import PyTrack, DVCParams
import tensorflow as tf
import numpy as np
import json


class LoadData(PyTrack):
    def __init__(self, id_=None, filter_=None):
        """Constructor oft the LoadData PyTrack Instance

        Parameters
        ----------
        id_: int, str, optional
            Optional primary key to query a previously created stage
        filter_: dict, optional
            Optional second method to query - only executed if id_ = None - using a dictionary with parameters key pairs
            This will always return the first instance. If multiple instances are possible use query_obj()!
        """
        super().__init__()
        self.dvc = DVCParams(
            outs=["x_train.npy", "y_train.npy", "x_test.npy", "y_test.npy"]
        )
        self.post_init(id_, filter_)

    def __call__(
        self,
        dataset: str,
        exec_: bool = False,
        slurm: bool = False,
        force: bool = False,
        always_changed: bool = False,
    ):
        """Call method of the LoadData class

        Parameters
        ----------
        dataset: str
            Name of the dataset
        force: bool, default=False
            Use dvc run with `--force` to overwrite previous stages!
        exec_: bool, default=False
            Run the stage directly and don't use dvc with '--no-exec'.
            This will not output stdout/stderr in real time and should only be used for fast functions!
        always_changed: bool, default=False
            Set the always changed dvc argument. See the official DVC docs. Can be useful for debugging / development.
        slurm: bool, default=False
            Use `SRUN` with self.slurm_config for this stage - WARNING this doesn't mean that every stage uses slurm
            and you may accidentally run stages on your HEAD Node. You can check the commands in dvc.yaml!

        Returns
        -------

        """
        self.parameters = {"dataset": dataset}
        self.post_call(
            exec_=exec_, slurm=slurm, force=force, always_changed=always_changed
        )

    def run(self):
        """Run method that loads the data

        Notes
        -----
            only mnist dataset is supported
        """
        self.pre_run()

        if self.parameters["dataset"] == "mnist":
            mnist = tf.keras.datasets.mnist
            (x_train, y_train), (x_test, y_test) = mnist.load_data()
            x_train, x_test = x_train / 255.0, x_test / 255.0

            with open(self.files.outs[0], "wb") as f:
                np.save(f, x_train)
            with open(self.files.outs[1], "wb") as f:
                np.save(f, y_train)
            with open(self.files.outs[2], "wb") as f:
                np.save(f, x_test)
            with open(self.files.outs[3], "wb") as f:
                np.save(f, y_test)

            self.results = {"shape": x_train.shape, "targets": len(np.unique(y_train))}


class FitModel(PyTrack):
    def __init__(self, id_=None, filter_=None):
        """Constructor oft the FitModel PyTrack Instance

        Parameters
        ----------
        id_: int, str, optional
            Optional primary key to query a previously created stage
        filter_: dict, optional
            Optional second method to query - only executed if id_ = None - using a dictionary with parameters key pairs
            This will always return the first instance. If multiple instances are possible use query_obj()!
        """
        super().__init__()
        self.dvc = DVCParams(outs=["model"])
        self.json_file = False
        self.post_init(id_, filter_)

    def __call__(
        self,
        exec_: bool = False,
        slurm: bool = False,
        force: bool = False,
        always_changed: bool = False,
    ):
        """Call method of the LoadData class

        Parameters
        ----------
        force: bool, default=False
            Use dvc run with `--force` to overwrite previous stages!
        exec_: bool, default=False
            Run the stage directly and don't use dvc with '--no-exec'.
            This will not output stdout/stderr in real time and should only be used for fast functions!
        always_changed: bool, default=False
            Set the always changed dvc argument. See the official DVC docs. Can be useful for debugging / development.
        slurm: bool, default=False
            Use `SRUN` with self.slurm_config for this stage - WARNING this doesn't mean that every stage uses slurm
            and you may accidentally run stages on your HEAD Node. You can check the commands in dvc.yaml!

        Returns
        -------

        """
        self.dvc.deps = LoadData(id_=0).files.outs[:2]

        self.parameters = {"layer": 128}
        self.post_call(
            exec_=exec_, slurm=slurm, force=force, always_changed=always_changed
        )

    def run(self):
        """Fit the model"""
        self.pre_run()

        load_data = LoadData(id_=0)

        input_shape = load_data.results["shape"][1:]
        target_size = load_data.results["targets"]

        model = tf.keras.models.Sequential(
            [
                tf.keras.layers.Flatten(input_shape=input_shape),
                tf.keras.layers.Dense(self.parameters["layer"], activation="relu"),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.Dense(target_size),
            ]
        )

        loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
        model.compile(optimizer="adam", loss=loss_fn, metrics=["accuracy"])

        with open(load_data.files.outs[0], "rb") as f:
            x_train = np.load(f)
        with open(load_data.files.outs[1], "rb") as f:
            y_train = np.load(f)

        model.fit(x_train, y_train, epochs=5)
        model.save(str(self.files.outs[0]))


class EvaluateModel(PyTrack):
    def __init__(self, id_=None, filter_=None):
        """Constructor oft the EvaluateModel PyTrack Instance

        Parameters
        ----------
        id_: int, str, optional
            Optional primary key to query a previously created stage
        filter_: dict, optional
            Optional second method to query - only executed if id_ = None - using a dictionary with parameters key pairs
            This will always return the first instance. If multiple instances are possible use query_obj()!
        """
        super().__init__()
        self.dvc = DVCParams(metrics_no_cache=["metrics.json"])
        self.json_file = False
        self.post_init(id_, filter_)

    def __call__(
        self,
        exec_: bool = False,
        slurm: bool = False,
        force: bool = False,
        always_changed: bool = False,
    ):
        """Call method of the LoadData class

        Parameters
        ----------
        force: bool, default=False
            Use dvc run with `--force` to overwrite previous stages!
        exec_: bool, default=False
            Run the stage directly and don't use dvc with '--no-exec'.
            This will not output stdout/stderr in real time and should only be used for fast functions!
        always_changed: bool, default=False
            Set the always changed dvc argument. See the official DVC docs. Can be useful for debugging / development.
        slurm: bool, default=False
            Use `SRUN` with self.slurm_config for this stage - WARNING this doesn't mean that every stage uses slurm
            and you may accidentally run stages on your HEAD Node. You can check the commands in dvc.yaml!

        Returns
        -------

        """
        self.parameters = {"verbose": 2}
        self.dvc.deps = FitModel(id_=0).files.outs
        self.dvc.deps += LoadData(id_=0).files.outs[2:]
        self.post_call(
            exec_=exec_, slurm=slurm, force=force, always_changed=always_changed
        )

    def run(self):
        """Evaluate the model"""
        self.pre_run()

        fit_model = FitModel(id_=0)

        model = tf.keras.models.load_model(str(fit_model.files.outs[0]))

        load_data = LoadData(id_=0)

        with open(load_data.files.outs[2], "rb") as f:
            x_test = np.load(f)
        with open(load_data.files.outs[3], "rb") as f:
            y_test = np.load(f)

        out = model.evaluate(x_test, y_test, verbose=self.parameters["verbose"])

        with open(self.files.metrics_no_cache[0], "w") as f:
            json.dump(out, f)
