"""
Unit tests for the qbraid device layer.
"""
import cirq
import numpy as np
import pytest
from braket.aws import AwsDevice
from braket.circuits import Circuit as BraketCircuit
from braket.devices import LocalSimulator as AwsSimulator
from braket.tasks.quantum_task import QuantumTask as BraketQuantumTask
from cirq.sim.simulator_base import SimulatorBase as CirqSimulator
from cirq.study.result import Result as CirqResult
from dwave.system.composites import EmbeddingComposite
from qiskit import QuantumCircuit as QiskitCircuit
from qiskit.providers.backend import Backend as QiskitBackend
from qiskit.providers.job import Job as QiskitJob

from qbraid import device_wrapper
from qbraid.devices._utils import SUPPORTED_VENDORS
from qbraid.devices.aws import BraketDeviceWrapper, BraketQuantumTaskWrapper
from qbraid.devices.google import CirqResultWrapper, CirqSimulatorWrapper
from qbraid.devices.ibm import QiskitBackendWrapper, QiskitJobWrapper


def device_wrapper_inputs(vendor: str):
    """Returns list of tuples containing all device_wrapper inputs for given vendor."""
    input_list = []
    for provider in SUPPORTED_VENDORS[vendor]:
        for device in SUPPORTED_VENDORS[vendor][provider]:
            input_list.append(device)
    return input_list


"""
Device wrapper tests: initialization
Coverage: all vendors, all available devices
"""
inputs_braket_dw = device_wrapper_inputs("aws")
inputs_braket_sampler = ["aws_dwave_2000Q_6", "aws_dwave_advantage_system1"]
inputs_cirq_dw = device_wrapper_inputs("google")
inputs_qiskit_dw = device_wrapper_inputs("ibm")


@pytest.mark.parametrize("device_id", inputs_braket_dw)
def test_init_braket_device_wrapper(device_id):
    qbraid_device = device_wrapper(device_id)
    vendor_device = qbraid_device.vendor_dlo
    assert isinstance(qbraid_device, BraketDeviceWrapper)
    assert isinstance(vendor_device, AwsSimulator) or isinstance(vendor_device, AwsDevice)


@pytest.mark.parametrize("device_id", inputs_braket_sampler)
def test_init_braket_dwave_sampler(device_id):
    qbraid_device = device_wrapper(device_id)
    vendor_sampler = qbraid_device.get_sampler()
    assert isinstance(vendor_sampler, EmbeddingComposite)


@pytest.mark.parametrize("device_id", inputs_cirq_dw)
def test_init_cirq_device_wrapper(device_id):
    qbraid_device = device_wrapper(device_id)
    vendor_device = qbraid_device.vendor_dlo
    assert isinstance(qbraid_device, CirqSimulatorWrapper)
    assert isinstance(vendor_device, CirqSimulator)


@pytest.mark.parametrize("device_id", inputs_qiskit_dw)
def test_init_qiskit_device_wrapper(device_id):
    qbraid_device = device_wrapper(device_id)
    vendor_device = qbraid_device.vendor_dlo
    assert isinstance(qbraid_device, QiskitBackendWrapper)
    assert isinstance(vendor_device, QiskitBackend)


"""
Device wrapper tests: run method
Coverage: all vendors, one device from each provider (calls to QPU's take time)
"""


def braket_circuit():
    circuit = BraketCircuit()
    circuit.h(0)
    circuit.ry(0, np.pi / 2)
    return circuit


def cirq_circuit(meas=True):
    q0 = cirq.GridQubit(0, 0)

    def basic_circuit():
        yield cirq.H(q0)
        yield cirq.Ry(rads=np.pi / 2)(q0)
        if meas:
            yield cirq.measure(q0, key="q0")

    circuit = cirq.Circuit()
    circuit.append(basic_circuit())
    return circuit


def qiskit_circuit(meas=True):
    circuit = QiskitCircuit(1, 1) if meas else QiskitCircuit(1)
    circuit.h(0)
    circuit.ry(np.pi / 2, 0)
    if meas:
        circuit.measure(0, 0)
    return circuit


circuits_braket_run = [braket_circuit(), cirq_circuit(False), qiskit_circuit(False)]
circuits_cirq_run = [cirq_circuit(), qiskit_circuit()]
circuits_qiskit_run = circuits_cirq_run
inputs_cirq_run = ["google_cirq_dm_sim"]
inputs_braket_run = ["aws_native_sv_sim", "aws_ionQ", "aws_rigetti_aspen9"]
inputs_qiskit_run = ["ibm_q_least_busy_qpu", "ibm_aer_qasm_sim", "ibm_aer_default_sim"]


@pytest.mark.parametrize("circuit", circuits_qiskit_run)
@pytest.mark.parametrize("device_id", inputs_qiskit_run)
def test_run_qiskit_device_wrapper(device_id, circuit):
    qbraid_device = device_wrapper(device_id)
    qbraid_job = qbraid_device.run(circuit, shots=10)
    vendor_job = qbraid_job.vendor_jlo
    assert isinstance(qbraid_job, QiskitJobWrapper)
    assert isinstance(vendor_job, QiskitJob)


@pytest.mark.parametrize("circuit", circuits_cirq_run)
@pytest.mark.parametrize("device_id", inputs_cirq_run)
def test_run_cirq_device_wrapper(device_id, circuit):
    qbraid_device = device_wrapper(device_id)
    qbraid_result = qbraid_device.run(circuit, repetitions=10)
    vendor_result = qbraid_result.vendor_rlo
    assert isinstance(qbraid_result, CirqResultWrapper)
    assert isinstance(vendor_result, CirqResult)


@pytest.mark.parametrize("circuit", circuits_braket_run)
@pytest.mark.parametrize("device_id", inputs_braket_run)
def test_run_braket_device_wrapper(device_id, circuit):
    qbraid_device = device_wrapper(device_id)
    qbraid_job = qbraid_device.run(circuit, shots=10)
    vendor_job = qbraid_job.vendor_jlo
    assert isinstance(qbraid_job, BraketQuantumTaskWrapper)
    assert isinstance(vendor_job, BraketQuantumTask)
