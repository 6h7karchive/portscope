"""Command-line interface for PortScope."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from portscope import __version__
from portscope.scanner import ScanResult, scan_ports


def parse_ports(value: str) -> list[int]:
    """Parse a comma-separated list of TCP ports."""
    try:
        ports = [int(part.strip()) for part in value.split(",")]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("ports must be comma-separated integers") from exc
    if not ports or any(not 1 <= port <= 65535 for port in ports):
        raise argparse.ArgumentTypeError("ports must be between 1 and 65535")
    if len(set(ports)) != len(ports):
        raise argparse.ArgumentTypeError("ports must not contain duplicates")
    return ports


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="portscope",
        description="Check explicitly specified TCP ports on a host you are authorized to test.",
    )
    parser.add_argument("host", help="hostname or IP address")
    parser.add_argument(
        "--ports",
        type=parse_ports,
        default=[22, 80, 443],
        help="comma-separated TCP ports (default: 22,80,443)",
    )
    parser.add_argument("--timeout", type=float, default=1.0, help="connection timeout in seconds")
    parser.add_argument("--concurrency", type=int, default=100, help="maximum concurrent checks")
    parser.add_argument("--json", dest="json_path", type=Path, help="write results to this JSON file")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def print_results(results: list[ScanResult]) -> None:
    print(f"{'HOST':<32} {'PORT':>5}  {'STATUS':<8} {'LATENCY':>10}")
    for result in results:
        latency = f"{result.latency_ms:.2f} ms" if result.latency_ms is not None else "-"
        print(f"{result.host:<32.32} {result.port:>5}  {result.status:<8} {latency:>10}")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")
    if not 1 <= args.concurrency <= 1024:
        parser.error("--concurrency must be between 1 and 1024")

    try:
        results = asyncio.run(scan_ports(args.host, args.ports, args.timeout, args.concurrency))
    except (ValueError, OSError) as exc:
        print(f"portscope: {exc}", file=sys.stderr)
        return 2

    print_results(results)
    if args.json_path:
        try:
            args.json_path.write_text(
                json.dumps([result.to_dict() for result in results], indent=2) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            print(f"portscope: could not write JSON: {exc}", file=sys.stderr)
            return 2
    return 0 if all(result.status == "open" for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
