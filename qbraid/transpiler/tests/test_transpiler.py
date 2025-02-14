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
Unit tests for the qbraid transpiler.

"""
import cirq
import numpy as np
import pytest
import pytket
import qiskit
from braket.circuits import Circuit as BraketCircuit
from braket.circuits import Gate as BraketGate
from braket.circuits import Instruction as BraketInstruction
from braket.circuits import gates as braket_gates
from cirq import Circuit as CirqCircuit
from pyquil import Program as pyQuilProgram
from pyquil import gates as pyquil_gates
from qiskit import QuantumCircuit as QiskitCircuit
from qiskit import QuantumRegister as QiskitQuantumRegister
from qiskit.circuit.quantumregister import Qubit as QiskitQubit

from qbraid import QbraidError, circuit_wrapper
from qbraid._qprogram import QPROGRAM_LIBS
from qbraid.exceptions import PackageValueError, ProgramTypeError
from qbraid.interface import convert_to_contiguous, to_unitary
from qbraid.interface.programs import bell_data, shared15_data
from qbraid.interface.qbraid_cirq._utils import _equal
from qbraid.transpiler.cirq_braket.tests._gate_archive import braket_gates as braket_gates_dict
from qbraid.transpiler.cirq_qasm.tests._gate_archive import cirq_gates as cirq_gates_dict
from qbraid.transpiler.cirq_qasm.tests._gate_archive import create_cirq_gate
from qbraid.transpiler.cirq_qiskit.tests._gate_archive import qiskit_gates as qiskit_gates_dict
from qbraid.transpiler.conversions import convert_from_cirq, convert_to_cirq
from qbraid.transpiler.exceptions import CircuitConversionError

TEST_15, UNITARY_15 = shared15_data()
TEST_BELL, UNITARY_BELL = bell_data()

# Cirq Bell circuit.
cirq_qreg = cirq.LineQubit.range(2)
cirq_qreg_rev = list(reversed(cirq_qreg))
cirq_circuit = cirq.Circuit(cirq.ops.H.on(cirq_qreg[0]), cirq.ops.CNOT.on(*cirq_qreg))
cirq_circuit_rev = cirq.Circuit(cirq.ops.H.on(cirq_qreg_rev[0]), cirq.ops.CNOT.on(*cirq_qreg_rev))

# Qiskit Bell circuit.
qiskit_qreg = qiskit.QuantumRegister(2)
qiskit_circuit = qiskit.QuantumCircuit(qiskit_qreg)
qiskit_circuit.h(qiskit_qreg[0])
qiskit_circuit.cnot(*qiskit_qreg)

# pyQuil Bell circuit.
pyquil_circuit = pyQuilProgram(pyquil_gates.H(0), pyquil_gates.CNOT(0, 1))

# Braket Bell circuit.
braket_circuit = BraketCircuit(
    [
        BraketInstruction(braket_gates.H(), 0),
        BraketInstruction(braket_gates.CNot(), [0, 1]),
    ]
)

# pytket Bell Circuit
pytket_circuit = pytket.Circuit(2)
pytket_circuit.H(0)
pytket_circuit.CX(0, 1)

circuit_types = {
    "cirq": cirq.Circuit,
    "qiskit": qiskit.QuantumCircuit,
    "pyquil": pyQuilProgram,
    "braket": BraketCircuit,
    "pytket": pytket.Circuit,
}


@pytest.mark.parametrize(
    "circuit", (qiskit_circuit, pyquil_circuit, braket_circuit, pytket_circuit)
)
def test_to_cirq(circuit):
    converted_circuit, input_type = convert_to_cirq(circuit)
    assert _equal(converted_circuit, cirq_circuit) or _equal(converted_circuit, cirq_circuit_rev)
    assert input_type in circuit.__module__


@pytest.mark.parametrize("item", [1, None])
def test_to_cirq_bad_types(item):
    with pytest.raises(ProgramTypeError):
        convert_to_cirq(item)


@pytest.mark.parametrize("item", ["DECLARE ro BIT[1]", "circuit"])
def test_to_cirq_bad_string(item):
    with pytest.raises(CircuitConversionError):
        convert_to_cirq(item)


@pytest.mark.parametrize("to_type", QPROGRAM_LIBS)
def test_from_cirq(to_type):
    converted_circuit = convert_from_cirq(cirq_circuit, to_type)
    circuit, input_type = convert_to_cirq(converted_circuit)
    assert _equal(circuit, cirq_circuit)
    assert input_type == to_type


@pytest.mark.parametrize("item", ["package", 1, None])
def test_from_cirq_bad_package(item):
    with pytest.raises(PackageValueError):
        convert_from_cirq(cirq_circuit, item)


def test_circuit_wrapper_error():
    """Test raising circuit wrapper error"""
    with pytest.raises(QbraidError):
        circuit_wrapper("Not a circuit")


def test_circuit_wrapper_error():
    """Test raising circuit wrapper error"""
    with pytest.raises(QbraidError):
        circuit_wrapper(None)


def test_transpile_package_error():
    """Test raising circuit wrapper error"""
    circuit = TEST_BELL["braket"]()
    wrapped = circuit_wrapper(circuit)
    with pytest.raises(PackageValueError):
        wrapped.transpile("Not a package")


def test_transpile_program_error():
    """Test raising circuit wrapper error"""
    circuit = TEST_BELL["braket"]()
    wrapped = circuit_wrapper(circuit)
    wrapped._program = None
    with pytest.raises(CircuitConversionError):
        wrapped.transpile("qiskit")


def shared_gates_test_data(package):
    """Returns data ``TestSharedGates``."""
    circuit = TEST_15[package]()
    qbraid_circuit = circuit_wrapper(circuit)
    return qbraid_circuit


def bell_test_data(package):
    """Returns data ``TestSharedGates``."""
    circuit = TEST_BELL[package]()
    qbraid_circuit = circuit_wrapper(circuit)
    return qbraid_circuit


# Define circuits and unitaries
target_packages = ["cirq", "qiskit", "braket", "pyquil", "pytket"]
data_test_15 = [shared_gates_test_data(name) for name in target_packages[:3]]
data_test_bell = [bell_test_data(name) for name in target_packages]


@pytest.mark.parametrize("qbraid_circuit", data_test_15)
@pytest.mark.parametrize("target_package", target_packages[:3])
def test_15(qbraid_circuit, target_package):
    """Tests transpiling circuits composed of gate types that share explicit support across
    multiple qbraid tranpsiler supported packages (qiskit, cirq, braket).
    """
    transpiled_circuit = qbraid_circuit.transpile(target_package)
    transpiled_unitary = to_unitary(transpiled_circuit)
    cirq.testing.assert_allclose_up_to_global_phase(transpiled_unitary, UNITARY_15, atol=1e-7)


@pytest.mark.parametrize("qbraid_circuit", data_test_bell)
@pytest.mark.parametrize("target_package", target_packages)
def test_bell(qbraid_circuit, target_package):
    """Tests transpiling bell circuits."""
    transpiled_circuit = qbraid_circuit.transpile(target_package)
    transpiled_unitary = to_unitary(transpiled_circuit)
    assert np.allclose(transpiled_unitary, UNITARY_BELL)


def nqubits_nparams(gate):
    if gate in ["H", "X", "Y", "Z", "S", "Sdg", "T", "Tdg", "I", "SX", "SXdg"]:
        return 1, 0
    elif gate in ["Phase", "RX", "RY", "RZ", "U1", "HPow", "XPow", "YPow", "ZPow"]:
        return 1, 1
    elif gate in ["R", "U2"]:
        return 1, 2
    elif gate in ["U", "U3"]:
        return 1, 3
    elif gate in ["CX", "CSX", "CH", "DCX", "Swap", "iSwap", "CY", "CZ"]:
        return 2, 0
    elif gate in ["RXX", "RXY", "RZX", "RYY", "CU1", "CRY", "RZZ", "CRZ", "CRX", "pSwap", "CPhase"]:
        return 2, 1
    elif gate in ["CCX", "RCCX"]:
        return 3, 0
    elif gate in ["CCZ"]:
        return 3, 1
    else:
        raise ValueError(f"Gate {gate} not accounted for")


def assign_params(init_gate1, init_gate2, nparams):
    params = np.random.random_sample(nparams) * np.pi
    return init_gate1(*params), init_gate2(*params)


def assign_params_cirq(gate_str, init_gate2, nparams):
    params = np.random.random_sample(nparams) * np.pi
    cirq_data = {"type": gate_str, "params": params, "matrix": None}
    new_cirq_gate = create_cirq_gate(cirq_data)
    return new_cirq_gate, init_gate2(*params)


def braket_gate_test_circuit(test_gate, nqubits, only_test_gate=False):
    qubits = [i for i in range(nqubits)] if nqubits > 1 else 0

    gates_qubits = [
        (BraketGate.H(), 0),
        (BraketGate.H(), 1),
        (BraketGate.H(), 2),
        (test_gate, qubits),
        (BraketGate.CNot(), [0, 1]),
        (BraketGate.Ry(np.pi), 2),
    ]

    if only_test_gate:
        gates_qubits = [(test_gate, qubits)]

    circuit = BraketCircuit([BraketInstruction(*gate_qubit) for gate_qubit in gates_qubits])

    unitary = to_unitary(circuit)
    qbraid_circuit = circuit_wrapper(circuit)

    return unitary, qbraid_circuit


def qiskit_gate_test_circuit(test_gate, nqubits):
    qreg = QiskitQuantumRegister(3, name="q")
    circuit = QiskitCircuit(qreg)
    circuit.h([0, 1, 2])
    qubits = [QiskitQubit(qreg, i) for i in range(nqubits)]
    circuit.append(test_gate, qubits)
    circuit.cx(0, 1)
    circuit.ry(np.pi, 2)

    unitary = to_unitary(circuit)
    qbraid_circuit = circuit_wrapper(circuit)

    return unitary, qbraid_circuit


def cirq_gate_test_circuit(test_gate, nqubits):
    circuit = CirqCircuit()
    q2, q1, q0 = [cirq.LineQubit(i) for i in range(3)]

    if nqubits == 1:
        input_qubits = [q0]
    elif nqubits == 2:
        input_qubits = [q0, q1]
    else:
        input_qubits = [q0, q1, q2]

    cirq_gate_test_gates = [
        cirq.H(q0),
        cirq.H(q1),
        cirq.H(q2),
        test_gate(*input_qubits),
        cirq.ry(rads=np.pi)(q2),
        cirq.CNOT(q0, q1),
    ]

    for gate in cirq_gate_test_gates:
        circuit.append(gate)

    unitary = to_unitary(circuit)
    qbraid_circuit = circuit_wrapper(circuit)

    return unitary, qbraid_circuit


braket_gate_set = set(braket_gates_dict.keys())
qiskit_gate_set = set(qiskit_gates_dict.keys())
cirq_gate_set = set(cirq_gates_dict.keys())

intersect_braket_qiskit = list(braket_gate_set.intersection(list(qiskit_gate_set)))
intersect_qiskit_cirq = list(qiskit_gate_set.intersection(list(cirq_gate_set)))
intersect_cirq_braket = list(cirq_gate_set.intersection(list(braket_gate_set)))

# skipping
intersect_braket_qiskit.remove("RXX")
intersect_braket_qiskit.remove("RYY")


@pytest.mark.parametrize("gate_str", intersect_braket_qiskit)
def test_gate_intersect_braket_qiskit(gate_str):
    braket_init_gate = braket_gates_dict[gate_str]
    qiskit_init_gate = qiskit_gates_dict[gate_str]
    nqubits, nparams = nqubits_nparams(gate_str)
    qiskt_gate, braket_gate = assign_params(qiskit_init_gate, braket_init_gate, nparams)
    braket_u, qbraid_braket_circ = braket_gate_test_circuit(braket_gate, nqubits)
    qiskit_u, qbraid_qiskit_circ = qiskit_gate_test_circuit(qiskt_gate, nqubits)
    cirq.testing.assert_allclose_up_to_global_phase(braket_u, qiskit_u, atol=1e-7)
    braket_circuit_transpile = qbraid_qiskit_circ.transpile("braket")
    qiskit_circuit_transpile = qbraid_braket_circ.transpile("qiskit")
    braket_transpile_u = to_unitary(braket_circuit_transpile)
    qiskit_transpile_u = to_unitary(qiskit_circuit_transpile)
    cirq.testing.assert_allclose_up_to_global_phase(braket_u, braket_transpile_u, atol=1e-7)
    cirq.testing.assert_allclose_up_to_global_phase(qiskit_u, qiskit_transpile_u, atol=1e-7)


@pytest.mark.parametrize("gate_str", intersect_qiskit_cirq)
def test_gate_intersect_qiskit_cirq(gate_str):
    qiskit_init_gate = qiskit_gates_dict[gate_str]
    nqubits, nparams = nqubits_nparams(gate_str)
    cirq_gate, qiskit_gate = assign_params_cirq(gate_str, qiskit_init_gate, nparams)
    cirq_u, qbraid_cirq_circ = cirq_gate_test_circuit(cirq_gate, nqubits)
    qiskit_u, qbraid_qiskit_circ = qiskit_gate_test_circuit(qiskit_gate, nqubits)
    cirq.testing.assert_allclose_up_to_global_phase(cirq_u, qiskit_u, atol=1e-7)
    qiskit_circuit_transpile = qbraid_cirq_circ.transpile("qiskit")
    cirq_circuit_transpile = qbraid_qiskit_circ.transpile("cirq")
    qiskit_transpile_u = to_unitary(qiskit_circuit_transpile)
    cirq_transpile_u = to_unitary(cirq_circuit_transpile)
    cirq.testing.assert_allclose_up_to_global_phase(cirq_u, cirq_transpile_u, atol=1e-7)
    cirq.testing.assert_allclose_up_to_global_phase(qiskit_u, qiskit_transpile_u, atol=1e-7)


@pytest.mark.parametrize("gate_str", intersect_cirq_braket)
def test_gate_intersect_braket_cirq(gate_str):
    braket_init_gate = braket_gates_dict[gate_str]
    nqubits, nparams = nqubits_nparams(gate_str)
    cirq_gate, braket_gate = assign_params_cirq(gate_str, braket_init_gate, nparams)
    cirq_u, qbraid_cirq_circ = cirq_gate_test_circuit(cirq_gate, nqubits)
    braket_u, qbraid_braket_circ = braket_gate_test_circuit(braket_gate, nqubits)
    cirq.testing.assert_allclose_up_to_global_phase(cirq_u, braket_u, atol=1e-7)
    braket_circuit_transpile = qbraid_cirq_circ.transpile("braket")
    cirq_circuit_transpile = qbraid_braket_circ.transpile("cirq")
    braket_transpile_u = to_unitary(braket_circuit_transpile)
    cirq_transpile_u = to_unitary(cirq_circuit_transpile)
    cirq.testing.assert_allclose_up_to_global_phase(cirq_u, cirq_transpile_u, atol=1e-7)
    cirq.testing.assert_allclose_up_to_global_phase(braket_u, braket_transpile_u, atol=1e-7)


yes_braket_no_qiskit = list(set(braket_gates_dict).difference(qiskit_gates_dict))
yes_qiskit_no_braket = list(set(qiskit_gates_dict).difference(braket_gates_dict))
yes_braket_no_cirq = list(set(braket_gates_dict).difference(cirq_gates_dict))
yes_cirq_no_braket = list(set(cirq_gates_dict).difference(braket_gates_dict))
yes_cirq_no_qiskit = list(set(cirq_gates_dict).difference(qiskit_gates_dict))
yes_qiskit_no_cirq = list(set(qiskit_gates_dict).difference(cirq_gates_dict))

NOT_SUPPORTED = ["RCCX", "RXX", "RYY", "RZX", "CSX", "CRX", "CRY", "U"]


@pytest.mark.parametrize("gate_str", yes_braket_no_qiskit)
def test_yes_braket_no_qiskit(gate_str):
    braket_init_gate = braket_gates_dict[gate_str]
    nqubits, nparams = nqubits_nparams(gate_str)
    params = np.random.random_sample(nparams) * np.pi
    braket_gate = braket_init_gate(*params)
    braket_u, qbraid_braket_circ = braket_gate_test_circuit(braket_gate, nqubits)
    qiskit_circuit = qbraid_braket_circ.transpile("qiskit")
    qiskit_u = to_unitary(qiskit_circuit)
    cirq.testing.assert_allclose_up_to_global_phase(braket_u, qiskit_u, atol=1e-7)


@pytest.mark.parametrize("gate_str", yes_qiskit_no_braket)
def test_yes_qiskit_no_braket(gate_str):
    qiskit_init_gate = qiskit_gates_dict[gate_str]
    nqubits, nparams = nqubits_nparams(gate_str)
    params = np.random.random_sample(nparams) * np.pi
    qiskit_gate = qiskit_init_gate(*params)
    qiskit_u, qbraid_qiskit_circ = qiskit_gate_test_circuit(qiskit_gate, nqubits)
    if gate_str in NOT_SUPPORTED:
        assert True
    else:
        braket_circuit = qbraid_qiskit_circ.transpile("braket")
        braket_u = to_unitary(braket_circuit)
        cirq.testing.assert_allclose_up_to_global_phase(qiskit_u, braket_u, atol=1e-7)


@pytest.mark.parametrize("gate_str", yes_qiskit_no_cirq)
def test_yes_qiskit_no_cirq(gate_str):
    qiskit_init_gate = qiskit_gates_dict[gate_str]
    nqubits, nparams = nqubits_nparams(gate_str)
    params = np.random.random_sample(nparams) * np.pi
    qiskit_gate = qiskit_init_gate(*params)
    qiskit_u, qbraid_qiskit_circ = qiskit_gate_test_circuit(qiskit_gate, nqubits)
    if gate_str in NOT_SUPPORTED:
        assert True
    else:
        cirq_circuit = qbraid_qiskit_circ.transpile("cirq")
        cirq_u = to_unitary(cirq_circuit)
        cirq.testing.assert_allclose_up_to_global_phase(qiskit_u, cirq_u, atol=1e-7)


@pytest.mark.parametrize("gate_str", yes_braket_no_cirq)
def test_yes_braket_no_cirq(gate_str):
    braket_init_gate = braket_gates_dict[gate_str]
    nqubits, nparams = nqubits_nparams(gate_str)
    params = np.random.random_sample(nparams) * np.pi
    braket_gate = braket_init_gate(*params)
    braket_u, qbraid_braket_circ = braket_gate_test_circuit(braket_gate, nqubits)
    cirq_circuit = qbraid_braket_circ.transpile("cirq")
    cirq_u = to_unitary(cirq_circuit)
    cirq.testing.assert_allclose_up_to_global_phase(braket_u, cirq_u, atol=1e-7)


@pytest.mark.parametrize("gate_str", yes_cirq_no_qiskit)
def test_yes_cirq_no_qiskit(gate_str):
    cirq_init_gate = cirq_gates_dict[gate_str]
    nqubits, nparams = nqubits_nparams(gate_str)
    exp = np.random.random()
    cirq_gate = cirq_init_gate(exponent=exp)
    cirq_u, qbraid_cirq_circ = cirq_gate_test_circuit(cirq_gate, nqubits)
    qiskit_circuit = qbraid_cirq_circ.transpile("qiskit")
    qiskit_u = to_unitary(qiskit_circuit)
    cirq.testing.assert_allclose_up_to_global_phase(cirq_u, qiskit_u, atol=1e-7)


@pytest.mark.parametrize("gate_str", yes_cirq_no_braket)
def test_yes_cirq_no_braket(gate_str):
    cirq_init_gate = cirq_gates_dict[gate_str]
    nqubits, nparams = nqubits_nparams(gate_str)
    if gate_str == "U3":
        params = np.random.random_sample(nparams)
        cirq_gate = cirq_init_gate(*params)
    else:
        exp = np.random.random()
        cirq_gate = cirq_init_gate(exponent=exp)
    cirq_u, qbraid_cirq_circ = cirq_gate_test_circuit(cirq_gate, nqubits)
    braket_circuit = qbraid_cirq_circ.transpile("braket")
    braket_u = to_unitary(braket_circuit)
    cirq.testing.assert_allclose_up_to_global_phase(cirq_u, braket_u, atol=1e-7)


def test_braket_transpile_ccnot():
    braket_circuit = BraketCircuit()
    braket_circuit.ccnot(2, 0, 1)
    braket_circuit.ccnot(3, 1, 0)
    qbraid_braket = circuit_wrapper(braket_circuit)
    qiskit_circuit = qbraid_braket.transpile("qiskit")
    braket_ccnot_unitary = to_unitary(braket_circuit)
    qiskit_ccnot_unitary = to_unitary(qiskit_circuit)
    cirq.testing.assert_allclose_up_to_global_phase(
        braket_ccnot_unitary, qiskit_ccnot_unitary, atol=1e-7
    )


def test_non_contiguous_qubits_braket():
    braket_circuit = BraketCircuit()
    braket_circuit.h(0)
    braket_circuit.cnot(0, 2)
    braket_circuit.cnot(2, 4)
    test_circuit = convert_to_contiguous(braket_circuit)
    qbraid_wrapper = circuit_wrapper(test_circuit)
    cirq_circuit = qbraid_wrapper.transpile("cirq")
    qiskit_circuit = qbraid_wrapper.transpile("qiskit")
    braket_unitary = to_unitary(test_circuit)
    cirq_unitary = to_unitary(cirq_circuit)
    qiskit_unitary = to_unitary(qiskit_circuit)
    cirq.testing.assert_allclose_up_to_global_phase(braket_unitary, cirq_unitary, atol=1e-7)
    cirq.testing.assert_allclose_up_to_global_phase(qiskit_unitary, braket_unitary, atol=1e-7)


def test_non_contiguous_qubits_cirq():
    cirq_circuit = CirqCircuit()
    q0 = cirq.LineQubit(4)
    q2 = cirq.LineQubit(2)
    q4 = cirq.LineQubit(0)
    cirq_circuit.append(cirq.H(q0))
    cirq_circuit.append(cirq.CNOT(q0, q2))
    cirq_circuit.append(cirq.CNOT(q2, q4))
    test_circuit = convert_to_contiguous(cirq_circuit)
    qbraid_wrapper = circuit_wrapper(test_circuit)
    qiskit_circuit = qbraid_wrapper.transpile("qiskit")
    braket_circuit = qbraid_wrapper.transpile("braket")
    cirq_unitary = to_unitary(test_circuit)
    qiskit_unitary = to_unitary(qiskit_circuit)
    braket_unitary = to_unitary(braket_circuit)
    cirq.testing.assert_allclose_up_to_global_phase(cirq_unitary, qiskit_unitary, atol=1e-7)
    cirq.testing.assert_allclose_up_to_global_phase(braket_unitary, cirq_unitary, atol=1e-7)
