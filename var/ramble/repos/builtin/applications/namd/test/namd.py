# Copyright 2022-2026 The Ramble Authors
#
# Licensed under the Apache License, Version 2.0 <LICENSE-APACHE or
# https://www.apache.org/licenses/LICENSE-2.0> or the MIT license
# <LICENSE-MIT or https://opensource.org/licenses/MIT>, at your
# option. This file may not be copied, modified, or distributed
# except according to those terms.

import json
import os

import pytest

import ramble.workspace
from ramble.main import RambleCommand

workspace = RambleCommand("workspace")

pytestmark = pytest.mark.usefixtures(
    "mutable_config",
    "mutable_mock_workspace_path",
)


def test_namd_inmem_foms_analysis(workspace_name):
    """Test that namd calculates Nanoseconds per day FOM in-memory without writing namd_nspd_stat.out"""
    global_args = ["-w", workspace_name]
    with ramble.workspace.create(workspace_name) as ws:
        workspace(
            "manage",
            "experiments",
            "namd",
            "--wf",
            "ApoA1",
            "-e",
            "test_exp",
            "-v",
            "n_nodes=1",
            "-v",
            "processes_per_node=1",
            "-v",
            "batch_submit={execute_experiment}",
            global_args=global_args,
        )
        workspace("setup", "--dry-run", global_args=global_args)

        run_dir = os.path.join(ws.experiment_dir, "namd", "ApoA1", "test_exp")
        log_out = os.path.join(run_dir, "test_exp.out")

        with open(log_out, "w", encoding="utf-8") as f:
            f.write(
                "Info: Benchmark time: 16 CPUs 0.025 s/step 0.25 days/ns 512.0 MB memory\n"
            )
            f.write("WallClock: 12.5 CPUTime: 12.0 Memory: 512.0 MB\n")
            f.write("End of program\n")

        workspace("analyze", "-f", "json", global_args=global_args)

        result_file = os.path.join(ws.results_dir, "results.latest.json")
        with open(result_file, encoding="utf-8") as f:
            results = json.load(f)

        exp_res = results["experiments"][0]
        assert exp_res["RAMBLE_STATUS"] == "SUCCESS"
        contexts_by_name = {ctx["name"]: ctx for ctx in exp_res["CONTEXTS"]}
        null_foms = {f["name"]: f for f in contexts_by_name["null"]["foms"]}

        assert null_foms["Benchmark days per nanosecond"]["value"] == "0.25"
        assert null_foms["Nanoseconds per day"]["value"] == "4.0"
        assert null_foms["Nanoseconds per day"]["units"] == "ns/day"
