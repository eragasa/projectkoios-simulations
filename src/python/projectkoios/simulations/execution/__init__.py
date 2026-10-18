"""Execute explicit calculator commands with durable failure records."""

from projectkoios.simulations.execution._executor import CalculatorExecutor
from projectkoios.simulations.execution._records import (
    CalculatorExecutionError,
    CalculatorExecutionRecord,
    CalculatorExecutionRequest,
    CalculatorOutputEmissionError,
    ExecutionStatus,
)

__all__ = (
    "CalculatorExecutionError",
    "CalculatorExecutionRecord",
    "CalculatorExecutionRequest",
    "CalculatorExecutor",
    "CalculatorOutputEmissionError",
    "ExecutionStatus",
)
