"""Bounded POSIX process-group termination mechanics."""

from __future__ import annotations

import contextlib
import os
import signal
import subprocess
import time
from dataclasses import dataclass

_PROCESS_GROUP_TERMINATION_GRACE_SECONDS = 0.5
_PROCESS_GROUP_POLL_SECONDS = 0.01
_PROCESS_GROUP_KILL_WAIT_SECONDS = 2.0


class _ProcessTerminationError(RuntimeError):
    """Report failure to establish bounded process-group termination."""


@dataclass(frozen=True, slots=True)
class _ProcessTerminationResult:
    """Carry the observed direct-process return code after group cleanup."""

    returncode: int


class _ProcessGroupSupport:
    """Provide patchable POSIX process-group mechanics to the executor."""

    __slots__ = ()

    def _terminate_process_group(
        self,
        process: subprocess.Popen[bytes],
    ) -> _ProcessTerminationResult:
        process_group_id = process.pid
        try:
            self._signal_process_group(process_group_id, signal.SIGTERM)
        except OSError as error:
            self._kill_direct_process_bounded(process)
            raise _ProcessTerminationError(
                f"failed to terminate process group {process_group_id}: {error}"
            ) from error
        deadline = time.monotonic() + _PROCESS_GROUP_TERMINATION_GRACE_SECONDS
        try:
            while (
                self._process_group_exists(process_group_id)
                and time.monotonic() < deadline
            ):
                process.poll()
                time.sleep(_PROCESS_GROUP_POLL_SECONDS)
            group_survived = self._process_group_exists(process_group_id)
        except OSError as error:
            self._kill_direct_process_bounded(process)
            raise _ProcessTerminationError(
                f"failed to inspect process group {process_group_id}: {error}"
            ) from error
        if group_survived:
            try:
                self._signal_process_group(process_group_id, signal.SIGKILL)
            except OSError as error:
                self._kill_direct_process_bounded(process)
                raise _ProcessTerminationError(
                    f"failed to kill process group {process_group_id}: {error}"
                ) from error
        kill_deadline = time.monotonic() + _PROCESS_GROUP_KILL_WAIT_SECONDS
        while time.monotonic() < kill_deadline:
            direct_process_reaped = process.poll() is not None
            try:
                process_group_gone = not self._process_group_exists(process_group_id)
            except OSError as error:
                self._kill_direct_process_bounded(process)
                raise _ProcessTerminationError(
                    f"failed to inspect process group {process_group_id}: {error}"
                ) from error
            if direct_process_reaped and process_group_gone:
                assert process.returncode is not None
                return _ProcessTerminationResult(process.returncode)
            time.sleep(_PROCESS_GROUP_POLL_SECONDS)
        raise _ProcessTerminationError(
            f"process group {process_group_id} did not terminate after kill"
        )

    def _kill_direct_process_bounded(
        self,
        process: subprocess.Popen[bytes],
    ) -> None:
        with contextlib.suppress(OSError):
            process.kill()
        with contextlib.suppress(subprocess.TimeoutExpired):
            process.wait(timeout=_PROCESS_GROUP_KILL_WAIT_SECONDS)

    def _signal_process_group(
        self,
        process_group_id: int,
        signal_number: int,
    ) -> None:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process_group_id, signal_number)

    def _process_group_exists(self, process_group_id: int) -> bool:
        try:
            os.killpg(process_group_id, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True
