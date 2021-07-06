# -*- coding: utf-8 -*-
# All rights reserved-2021©.
import numpy as np
import pytest

from qbraid import circuits
import qbraid.circuits.update_rule
from qbraid.circuits.circuit import Circuit
from qbraid.circuits.exceptions import CircuitError
from qbraid.circuits.moment import Moment
from qbraid.circuits.instruction import Instruction
from qbraid.circuits.update_rule import UpdateRule

def get_qubit_idx_dict(dict: dict = None) -> None:
    # get index of qubits
    check_qubit = []
    for qubit_obj in dict["_qubits"]:
        check_qubit.append(qubit_obj._index)
    dict["_qubits"] = check_qubit


def circuit():
    return Circuit(num_qubits=3, name="test_circuit")


@pytest.fixture()
def gate():
    return circuits.H()


@pytest.fixture()
def instruction(gate):
    return Instruction(gate=gate, qubits=[0])

@pytest.fixture()
def two_same_instructions():
    return [
        Instruction(gate=circuits.CH(), qubits=[1, 2]),
        Instruction(gate=circuits.CH(), qubits=[1, 2]),
    ]


@pytest.fixture()
def two_diff_instructions():
    return [
        Instruction(gate=circuits.I(), qubits=[1]),
        Instruction(gate=circuits.RZX(theta=0), qubits=[3, 2]),
    ]


@pytest.fixture()
def moment(instruction):
    return Moment(instructions=instruction)


"""
INSTRUCTIONS
"""


def test_instruction_creation(instruction):
    """Test Instruction Object Creation. """
    assert [type(instruction), type(instruction.gate), type(instruction.qubits)] == [
        Instruction,
        circuits.H,
        list,
    ]


def test_too_many_qubits(gate):
    """Test gate with too many qubits."""
    with pytest.raises(AttributeError):
        Instruction(gate=gate, qubits=[1, 2, 3])
        print(Instruction.qubits)


def test_too_few_qubits(gate):
    """Test gate with too few qubits. """
    with pytest.raises(AttributeError):
        Instruction(gate=circuit.CH(), qubits=[1])
        print(Instruction.qubits)


def test_no_qubits(gate):
    """Test gate with no qubits."""
    with pytest.raises(AttributeError):
        Instruction(gate=circuit.CH())
        print(Instruction.qubits)


def test_invalid_gate(gate):
    """Test invalid gate."""
    with pytest.raises(AttributeError):
        Instruction(gate="SWAP", qubits=[1, 2])


def test_control_gate(gate):
    """Test Instruction Parameters."""
    print(Instruction(gate=circuits.CH(), qubits=[1, 2]))


"""
MOMENTS
"""


def test_moment_w_instruction(moment):
    # check class parameter
    """Test moment with an instruction always should be a list."""
    print(moment)
    assert type(moment.instructions) == list


def test_not_instruction(moment):
    """Test moment with not instruction type appended."""
    with pytest.raises(TypeError):
        moment.append(5)


def test_append_set(moment,two_diff_instructions):
    """Test moment with nested list, works since recursively unpacks instructions."""
    moment.append([{*two_diff_instructions}])
    print(f"The instructions in the moment: {moment.instructions}")
    print(f"The qubits in the moment: {moment.qubits}")
    assert len(moment.instructions) == 3


def test_nested_list(moment):
    """Test moment with nested list, works since recursively unpacks instructions."""
    instruction1 = Instruction(gate=circuits.DCX(), qubits=[1, 2])
    moment.append([[instruction1]])
    print(f"The instructions in the moment: {moment.instructions}")
    print(f"The qubits in the moment: {moment.qubits}")
    assert len(moment.instructions) == 2


def test_add_operators_on_same_qubit(moment, two_same_instructions):
    """Test adding two instructions acting onsame qubits."""
    print(f"The instructions in the moment: {moment.instructions}")
    print(f"The qubits in the moment: {moment.qubits}")
    with pytest.raises(CircuitError):
        moment.append(two_same_instructions)


def test_same_qubit_at_a_time(moment, two_same_instructions):
    """Test adding two instructions acting on the same qubits."""
    print(f"The instructions in the moment: {moment.instructions}")
    print(f"The qubits in the moment: {moment.qubits}")
    with pytest.raises(CircuitError):
        for instruction in two_same_instructions:
            moment.append(instruction)


def test_add_operators_on_diff_qubit(moment):
    """Test adding two instructions acting on diff qubits."""
    CH1 = Instruction(gate=circuits.CH(), qubits=[1, 2])
    CH2 = Instruction(gate=circuits.CH(), qubits=[3, 4])
    print(f"The instructions in the moment: {moment.instructions}")
    print(f"The qubits in the moment: {moment.qubits}")
    moment.append([CH1, CH2])
    assert len(moment.instructions) == 3


"""
CIRCUITS
"""


def test_circuit_str():
    """Test str result"""
    circuit = Circuit(num_qubits=3, name="test_circuit")
    assert circuit.__str__() == "Circuit (test_circuit, 3 qubits, 0 gates)"

def test_unrecognized_update_rule(gate):
    """Test fake update rule."""
    h1 = Instruction(gate,0)
    h2 = Instruction(gate,1)
    h3 = Instruction(gate,2)
    circuit = Circuit(num_qubits=3, name="test_circuit",update_rule="Not Updating")
    with pytest.raises(CircuitError):
        circuit.append(h1)
        circuit.append(h2)
        circuit.append(h3)
    print(circuit.instructions)
    print(circuit.moments)
    

def test_inline_update_rule(gate):
    """Test inline update rule indivdually"""
    h1 = Instruction(gate,0)
    h2 = Instruction(gate,1)
    h3 = Instruction(gate,2)
    circuit = Circuit(num_qubits=3, name="test_circuit",update_rule=UpdateRule.INLINE)
    circuit.append(h1)
    circuit.append(h2)
    circuit.append(h3)
    print(circuit.instructions)
    print(circuit.moments)
    assert len(circuit.instructions) == 3

def test_inline_update_rule_together(gate):
    """Test inline update rule as list"""
    h1 = Instruction(gate,0)
    h2 = Instruction(gate,1)
    h3 = Instruction(gate,2)
    circuit = Circuit(num_qubits=3, name="test_circuit",update_rule=UpdateRule.INLINE)
    circuit.append([h1,h2,h3])
    print(circuit.instructions)
    print(circuit.moments)
    assert len(circuit.instructions) == 3

def test_new_update_rule(gate):
    """Test new update rule as list"""
    h1 = Instruction(gate,0)
    h2 = Instruction(gate,1)
    h3 = Instruction(gate,2)
    circuit = Circuit(num_qubits=3, name="test_circuit",update_rule=UpdateRule.NEW)
    circuit.append(h1)
    circuit.append(h2)
    circuit.append(h3)
    print(circuit.instructions)
    print(circuit.moments)
    assert len(circuit.moments) == 3

def test_new_update_rule_together(gate):
    """Test new update rule as list"""
    h1 = Instruction(gate,0)
    h2 = Instruction(gate,1)
    h3 = Instruction(gate,2)
    circuit = Circuit(num_qubits=3, name="test_circuit",update_rule=UpdateRule.NEW)
    circuit.append([h1,h2,h3])
    print(circuit.instructions)
    print(circuit.moments)
    assert len(circuit.moments) == 3

def test_earliest_update_rule(gate):
    """Test earliest update rule as list"""
    h1 = Instruction(gate,0)
    h2 = Instruction(gate,1)
    h3 = Instruction(gate,2)
    circuit = Circuit(num_qubits=3, name="test_circuit",update_rule=UpdateRule.EARLIEST)
    circuit.append(h1)
    circuit.append(h2)
    circuit.append(h3)
    print(circuit.instructions)
    print(circuit.moments)
    assert len(circuit.moments) == 1

def test_earliest_update_rule_together(gate):
    """Test earliest update rule as list"""
    h1 = Instruction(gate,0)
    h2 = Instruction(gate,1)
    h3 = Instruction(gate,1)
    circuit = Circuit(num_qubits=3, name="test_circuit",update_rule=UpdateRule.EARLIEST)
    circuit.append([h1,h2,h3])
    print(circuit.instructions)
    print(circuit.moments)
    assert len(circuit.moments) == 2


def test_new_then_inline_rule(gate):
    """Test new then inline update rule. 
        There is a distinction here between the below test_new_then_inline_rule_together()
        because this will create a new moment every time append is called.
    """
    h1 = Instruction(gate,1)
    h2 = Instruction(gate,1)
    h3 = Instruction(gate,2)
    h4 = Instruction(gate,2)
    circuit = Circuit(num_qubits=3, name="test_circuit",update_rule=UpdateRule.NEW_THEN_INLINE)
    circuit.append(h1)
    circuit.append(h2)
    circuit.append(h3)
    circuit.append(h4)
    print(circuit.instructions)
    print(circuit.moments)
    assert len(circuit.moments) == 4

def test_new_then_inline_rule_together(gate):
    """Test new then inline update rule """
    h1 = Instruction(gate,1)
    h2 = Instruction(gate,1)
    h3 = Instruction(gate,2)
    h4 = Instruction(gate,2)
    circuit = Circuit(num_qubits=3, name="test_circuit",update_rule=UpdateRule.NEW_THEN_INLINE)
    circuit.append([h1,h2,h3,h4])
    print(circuit.instructions)
    print(circuit.moments)
    assert len(circuit.moments) == 3

@pytest.mark.parametrize(
    "circuit_param, expected",
    [
        (
            circuit(),
            {
                "_qubits": [0, 1, 2],
                "_moments": [],
                "name": "test_circuit",
                "update_rule": qbraid.circuits.update_rule.UpdateRule.NEW_THEN_INLINE,
            },
        ),
    ],
)
def test_creating_circuit(circuit_param, expected):
    """ Test creating a circuit."""
    # check class parameters
    dict = circuit_param.__dict__.copy()
    get_qubit_idx_dict(dict)
    assert dict == expected


@pytest.mark.parametrize(
    "circuit_param, expected",
    [
        (
            circuit(),
            {
                "_qubits": [0, 1, 2],
                "_moments": [Moment("[]"), Moment("[]")],
                "name": "test_circuit",
                "update_rule": qbraid.circuits.update_rule.UpdateRule.NEW_THEN_INLINE,
            },
        )
    ],
)
def test_add_moment(circuit_param, expected):
    """ Test adding a moment."""
    moment = Moment()
    circuit_param.append(moment)
    dict = circuit_param.__dict__.copy()
    assert len(dict["_moments"]) == len(expected["_moments"])


