import asyncio

import pytest

from portscope.cli import parse_ports
from portscope.scanner import check_port, scan_ports


def test_parse_ports():
    assert parse_ports("22, 80,443") == [22, 80, 443]


@pytest.mark.parametrize("value", ["0", "65536", "80,nope", "80,80", ""])
def test_parse_ports_rejects_invalid_input(value):
    with pytest.raises(Exception):
        parse_ports(value)


@pytest.mark.asyncio
async def test_check_port_open():
    server = await asyncio.start_server(lambda r, w: w.close(), "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    try:
        result = await check_port("127.0.0.1", port, timeout=1)
        assert result.status == "open"
        assert result.latency_ms is not None
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_scan_ports_validates_ports():
    with pytest.raises(ValueError):
        await scan_ports("localhost", [0])


@pytest.mark.asyncio
async def test_scan_ports_rejects_empty_host():
    with pytest.raises(ValueError):
        await scan_ports("  ", [80])
