from ...gate import Gate
from typing import Optional


class RXY(Gate):
    def __init__(self, theta: float, global_phase: Optional[float] = 0.0):
        super().__init__("RXY", num_qubits=2, params=[theta], global_phase=global_phase)
