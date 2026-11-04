"""Execute explicit calculator commands with durable failure records."""

from projectkoios.simulations.execution._evidence import (
    CalculatorExecutionArtifactObservation,
    CalculatorExecutionContentIdentity,
    CalculatorExecutionObservation,
    CalculatorExecutionObservationAssembler,
    CalculatorExecutionObservationRequest,
    CalculatorExitCode,
    CalculatorExitDisposition,
    CalculatorNormalExit,
    CalculatorProcessTermination,
    CalculatorSignalTermination,
    CalculatorTimeout,
)
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
from projectkoios.simulations.execution._record_serialization import (
    CalculatorExecutionRecordSerializer,
)
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
    "CalculatorExecutionArtifactObservation",
    "CalculatorExecutionContentIdentity",
    "CalculatorExecutionError",
    "CalculatorExecutionObservation",
    "CalculatorExecutionObservationAssembler",
    "CalculatorExecutionObservationRequest",
    "CalculatorExecutionRecord",
    "CalculatorExecutionRequest",
    "CalculatorExecutionRecordSerializer",
    "CalculatorExecutor",
    "CalculatorExitCode",
    "CalculatorExitDisposition",
    "CalculatorNormalExit",
    "CalculatorOutputEmissionError",
    "CalculatorProcessTermination",
    "CalculatorSignalTermination",
    "CalculatorTimeout",
    "ExecutionStatus",
)
