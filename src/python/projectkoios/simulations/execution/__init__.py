"""Execute explicit calculator commands with durable failure records."""

from projectkoios.simulations.execution._executable import (
    CalculatorExecutableBinding,
    CalculatorExecutableIdentity,
    CalculatorExecutablePreparationFailure,
    CalculatorExecutablePreparationFailureCode,
    CalculatorExecutablePreparationResult,
    CalculatorExecutablePreparer,
    CalculatorPreparedExecutable,
)
from projectkoios.simulations.execution._executor import CalculatorExecutor
from projectkoios.simulations.execution._records import (
    CalculatorExecutionError,
    CalculatorExecutionRecord,
    CalculatorExecutionRequest,
    CalculatorOutputEmissionError,
    ExecutionStatus,
)

__all__ = (
    "CalculatorExecutableBinding",
    "CalculatorExecutableIdentity",
    "CalculatorExecutablePreparationFailure",
    "CalculatorExecutablePreparationFailureCode",
    "CalculatorExecutablePreparationResult",
    "CalculatorExecutablePreparer",
    "CalculatorPreparedExecutable",
    "CalculatorExecutionError",
    "CalculatorExecutionRecord",
    "CalculatorExecutionRequest",
    "CalculatorExecutor",
    "CalculatorOutputEmissionError",
    "ExecutionStatus",
)
