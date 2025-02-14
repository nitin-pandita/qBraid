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
Module defining exceptions for errors raised while handling circuits.

"""

from qbraid.exceptions import QbraidError


class CircuitConversionError(QbraidError):
    """Base class for errors raised while converting a circuit."""


class QasmError(QbraidError):
    """For errors raised while converting circuits to/from QASM."""
