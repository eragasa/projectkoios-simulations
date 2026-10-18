"""Chunked calculator stream capture and live emission mechanics."""

from __future__ import annotations

import contextlib
import os
import select
import sys
import threading
from dataclasses import dataclass
from typing import BinaryIO, cast

_STREAM_CHUNK_SIZE = 64 * 1024
_STREAM_POLL_SECONDS = 0.05


@dataclass(frozen=True, slots=True)
class _StreamPumpFailure:
    """Retain one stream capture or live-emission failure for terminal recording."""

    stream_name: str
    stage: str
    error: Exception


@dataclass(frozen=True, slots=True)
class _StreamPump:
    """Retain one source pipe and its active chunked drain thread."""

    stream_name: str
    source: BinaryIO
    stop: threading.Event
    emission_enabled: threading.Event
    thread: threading.Thread
    failures: list[_StreamPumpFailure]


class _StreamSupport:
    """Provide patchable stream mechanics to the calculator executor."""

    __slots__ = ()

    def _start_stream_pump(
        self,
        *,
        name: str,
        source: BinaryIO,
        destination: BinaryIO,
        failures: list[_StreamPumpFailure],
    ) -> _StreamPump:
        stop = threading.Event()
        emission_enabled = threading.Event()
        emission_enabled.set()
        thread = threading.Thread(
            name=f"calculator-{name}-pump",
            target=self._pump_stream,
            kwargs={
                "name": name,
                "source": source,
                "destination": destination,
                "stop": stop,
                "emission_enabled": emission_enabled,
                "failures": failures,
            },
            daemon=True,
        )
        thread.start()
        return _StreamPump(
            stream_name=name,
            source=source,
            stop=stop,
            emission_enabled=emission_enabled,
            thread=thread,
            failures=failures,
        )

    def _pump_stream(
        self,
        *,
        name: str,
        source: BinaryIO,
        destination: BinaryIO,
        stop: threading.Event,
        emission_enabled: threading.Event,
        failures: list[_StreamPumpFailure],
    ) -> None:
        capture_enabled = True
        file_descriptor = source.fileno()
        os.set_blocking(file_descriptor, False)
        while not stop.is_set():
            try:
                readable, _, _ = select.select(
                    [file_descriptor],
                    [],
                    [],
                    _STREAM_POLL_SECONDS,
                )
                if not readable:
                    continue
                chunk = os.read(file_descriptor, _STREAM_CHUNK_SIZE)
            except BlockingIOError:
                continue
            except Exception as error:
                if not stop.is_set():
                    failures.append(_StreamPumpFailure(name, "read", error))
                return
            if not chunk:
                return
            if capture_enabled:
                try:
                    self._write_and_flush(destination, chunk)
                except Exception as error:
                    failures.append(_StreamPumpFailure(name, "capture", error))
                    capture_enabled = False
            if emission_enabled.is_set():
                try:
                    self._emit_output(name, chunk)
                except Exception as error:
                    failures.append(_StreamPumpFailure(name, "emission", error))
                    emission_enabled.clear()

    def _finish_stream_pumps(
        self,
        pumps: tuple[_StreamPump, ...],
        *,
        abort_reads: bool = False,
    ) -> None:
        if abort_reads:
            for pump in pumps:
                pump.stop.set()
                with contextlib.suppress(OSError):
                    pump.source.close()
        for pump in pumps:
            pump.thread.join()
        if not abort_reads:
            for pump in pumps:
                pump.source.close()

    def _emit_output(self, stream_name: str, chunk: bytes) -> None:
        stream: object
        if stream_name == "stdout":
            stream = sys.stdout
        elif stream_name == "stderr":
            stream = sys.stderr
        else:
            raise ValueError(f"unsupported output stream: {stream_name}")
        candidate = getattr(stream, "buffer", None)
        if candidate is None:
            raise RuntimeError(f"parent {stream_name} does not expose a binary buffer")
        self._write_and_flush(cast(BinaryIO, candidate), chunk)

    def _write_and_flush(self, destination: BinaryIO, chunk: bytes) -> None:
        offset = 0
        while offset < len(chunk):
            written = destination.write(chunk[offset:])
            if written is None or written <= 0:
                raise OSError("output stream did not accept bytes")
            offset += written
        destination.flush()

    def _stream_failure_message(
        self,
        failures: list[_StreamPumpFailure],
    ) -> str:
        return "; ".join(
            f"{failure.stream_name} {failure.stage} failed: {failure.error}"
            for failure in failures
        )

    def _combine_error_message(
        self,
        primary: str,
        failures: list[_StreamPumpFailure],
    ) -> str:
        if not failures:
            return primary
        return f"{primary}; {self._stream_failure_message(failures)}"
