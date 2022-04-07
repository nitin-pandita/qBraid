# Copyright (C) 2020 Unitary Fund
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Unit tests for conversions between Cirq circuits and Qiskit circuits."""
import cirq
import numpy as np
import pytest

from qbraid.interface import circuits_allclose
from qbraid.transpiler.cirq_qiskit.conversions import to_qiskit


def test_bell_state_to_qiskit():
    """Tests cirq.Circuit --> qiskit.QuantumCircuit --> cirq.Circuit
    with a Bell state circuit.
    """
    qreg = cirq.LineQubit.range(2)
    cirq_circuit = cirq.Circuit([cirq.ops.H.on(qreg[0]), cirq.ops.CNOT.on(qreg[0], qreg[1])])
    qiskit_circuit = to_qiskit(cirq_circuit)
    print()
    print(cirq_circuit)
    print()
    print(qiskit_circuit)
    print()
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


@pytest.mark.parametrize("num_qubits", [1, 2, 3, 4, 5])
def test_random_circuit_to_qiskit(num_qubits):
    for i in range(10):
        cirq_circuit = cirq.testing.random_circuit(
            qubits=num_qubits,
            n_moments=np.random.randint(1, 6),
            op_density=1,
            random_state=np.random.randint(1, 10),
        )
        qiskit_circuit = to_qiskit(cirq_circuit)
        equal = circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)
        if not equal:
            print(qiskit_circuit)
            assert False
        else:
            assert True
