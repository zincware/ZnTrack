"""
This program and the accompanying materials are made available under the terms of the
Eclipse Public License v2.0 which accompanies this distribution, and is available at
https://www.eclipse.org/legal/epl-v20.html
SPDX-License-Identifier: EPL-2.0

Copyright Contributors to the Zincware Project.

Description: 
"""
from zntrack import Node, dvc, zn
from zntrack.core.data_classes import DVCOptions, DVCParams, ZnFiles
import os


def test_dvc_options(tmp_path):
    dvc_options = DVCOptions(
        no_commit=True,
        external=True,
        always_changed=True,
        no_exec=True,
        force=True,
        no_run_cache=True,
    )

    assert dvc_options.dvc_arguments == [
        "--no-commit",
        "--external",
        "--always-changed",
        "--no-exec",
        "--force",
        "--no-run-cache",
    ]


def test_dvc_params_update(tmp_path):
    os.chdir(tmp_path)

    dvc_params = DVCParams()

    dvc_params.update(value="deps.json", option="deps")
    dvc_params.update(value="outs.json", option="outs")

    assert dvc_params.dvc_arguments == ["--deps", "deps.json", "--outs", "outs.json"]


def test_dvc_params_update_node_dvc(tmp_path):
    os.chdir(tmp_path)

    @Node()
    class DVCTest:
        outs = dvc.outs("outs_file.txt")
        second_outs = dvc.outs("2outs_file.txt")

        def run(self):
            pass

    dvc_params = DVCParams()
    dvc_params.update(value=DVCTest(load=True), option="deps")

    assert dvc_params.dvc_arguments == [
        "--deps",
        "outs_file.txt",
        "--deps",
        "2outs_file.txt",
    ]


def test_dvc_params_update_node_zn(tmp_path):
    os.chdir(tmp_path)

    @Node()
    class DVCTest:
        outs = dvc.outs("outs_file.txt")
        result = zn.outs()

        def run(self):
            pass

    dvc_params = DVCParams()
    dvc_params.update(value=DVCTest(load=True), option="deps")

    assert dvc_params.dvc_arguments == [
        "--deps",
        "outs_file.txt",
        "--deps",
        "nodes/DVCTest/outs.json",
    ]


def test_dvc_params_update_node_zn2(tmp_path):
    os.chdir(tmp_path)

    @Node()
    class DVCTest:
        result = zn.outs()
        metrics = zn.metrics()

        def run(self):
            pass

    dvc_params = DVCParams()
    dvc_params.update(value=DVCTest(load=True), option="deps")

    assert dvc_params.dvc_arguments == [
        "--deps",
        "nodes/DVCTest/outs.json",
        "--deps",
        "nodes/DVCTest/metrics_no_cache.json",
    ]


def test_dvc_params_affected_files(tmp_path):
    os.chdir(tmp_path)

    dvc_params = DVCParams()

    dvc_params.update(value="deps.json", option="deps")

    for file_id in range(10):
        dvc_params.update(value=f"file_{file_id}", option="outs")
    # deps should not be in affected files
    assert dvc_params.affected_files == [f"file_{x}" for x in range(10)]


def test_dvc_params_internals(tmp_path):
    os.chdir(tmp_path)

    dvc_params = DVCParams()

    internal_test = {"a": 1, "b": "test", "c": {"nested": True}}

    dvc_params.internals = internal_test

    assert dvc_params.internals == internal_test


def test_zn_files():
    pass
    # TODO add missing tests for ZnFiles!
