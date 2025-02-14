# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Benchmarking tests for pyquil conversions

"""
import string

import numpy as np
import pyquil

import qbraid

#############
### BASE ####
#############

PYQUIL_BASELINE = 84
ALLOWANCE = 2

#############
### UTILS ###
#############


def generate_params(varnames):
    params = {}
    rot_args = ["angle", "phi", "lam", "gamma"]
    for ra in rot_args:
        if ra in varnames:
            params[ra] = np.random.rand() * 2 * np.pi

    if "qubit" in varnames:
        params["qubit"] = 0

    if "control" in varnames:
        params["control"] = 0
        params["target"] = 1

    if "q1" in varnames:
        params["q1"] = 0
        params["q2"] = 1

    return params


def get_pyquil_gates():
    pyquil_gates = {attr: None for attr in dir(pyquil.gates) if attr[0] in string.ascii_uppercase}

    for gate in pyquil_gates:
        try:
            params = generate_params(getattr(pyquil.gates, gate).__code__.co_varnames)
            pyquil_gates[gate] = getattr(pyquil.gates, gate)(**params)
        except Exception as e:
            continue

    return {k: v for k, v in pyquil_gates.items() if v is not None}


#############
### TESTS ###
#############

TARGETS = ["braket", "cirq", "pytket", "qiskit"]
pyquil_gates = get_pyquil_gates()
paramslist = [(target, gate) for target in TARGETS for gate in pyquil_gates]
failures = {}


def convert_from_pyquil_to_x(target, gate_name):
    gate = pyquil_gates[gate_name]
    source_circuit = pyquil.Program()
    source_circuit += gate
    target_circuit = qbraid.circuit_wrapper(source_circuit).transpile(target)
    assert qbraid.interface.circuits_allclose(source_circuit, target_circuit, strict_gphase=False)


def test_pyquil_coverage():
    for target in TARGETS:
        for gate_name in pyquil_gates:
            try:
                convert_from_pyquil_to_x(target, gate_name)
            except Exception as e:
                failures[f"{target}-{gate_name}"] = e

    total_tests = len(pyquil_gates) * len(TARGETS)
    nb_fails = len(failures)
    nb_passes = total_tests - nb_fails

    print(
        f"A total of {len(pyquil_gates)} gates were tested (for a total of {total_tests} tests). {nb_fails}/{total_tests} tests failed ({nb_fails / (total_tests):.2%}) and {nb_passes}/{total_tests} passed."
    )
    print("Failures:", failures.keys())

    assert (
        nb_passes >= PYQUIL_BASELINE - ALLOWANCE
    ), f"The coverage threshold was not met. {nb_fails}/{total_tests} tests failed ({nb_fails / (total_tests):.2%}) and {nb_passes}/{total_tests} passed (expected >= {PYQUIL_BASELINE}).\nFailures: {failures.keys()}\n\n"
