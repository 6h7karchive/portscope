"""Asynchronous TCP connection checks for explicitly specified ports."""

from __future__ import annotations

import asyncio
import time
from dataclasses import asdict, dataclass
from typing import Literal

Status = Literal["open", "closed", "timeout", "error"]


@dataclass(frozen=True, slots=True)
class ScanResult:
    host: str
    port: int
    status: Status
    latency_ms: float | None
    error: str | None = None

    def to_dict(self) -> dict[str, str | int | float | None]:
        """Return a JSON-serializable representation."""
        return asdict(self)


async def check_port(host: str, port: int, timeout: float = 1.0) -> ScanResult:
    """Attempt a TCP connection and classify the outcome."""
    started = time.perf_counter()
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
    except TimeoutError:
        return ScanResult(host, port, "timeout", None, f"connection timed out after {timeout:g}s")
    except OSError as exc:
        elapsed = round((time.perf_counter() - started) * 1000, 2)
        if isinstance(exc, ConnectionRefusedError):
            return ScanResult(host, port, "closed", elapsed, "connection refused")
        return ScanResult(host, port, "error", elapsed, str(exc))
    else:
        elapsed = round((time.perf_counter() - started) * 1000, 2)
        writer.close()
        try:
            await writer.wait_closed()
        except OSError:
            pass
        return ScanResult(host, port, "open", elapsed)


async def scan_ports(
    host: str,
    ports: list[int],
    timeout: float = 1.0,
    concurrency: int = 100,
) -> list[ScanResult]:
    """Check a list of ports with a bounded number of concurrent connections."""
    if not host.strip():
        raise ValueError("host must not be empty")
    if not 0 < timeout:
        raise ValueError("timeout must be greater than zero")
    if not 1 <= concurrency <= 1024:
        raise ValueError("concurrency must be between 1 and 1024")
    if any(isinstance(port, bool) or not 1 <= port <= 65535 for port in ports):
        raise ValueError("ports must be integers between 1 and 65535")

    semaphore = asyncio.Semaphore(concurrency)

    async def bounded_check(port: int) -> ScanResult:
        async with semaphore:
            return await check_port(host, port, timeout)

    return await asyncio.gather(*(bounded_check(port) for port in ports))
