# PortScope

A small asynchronous TCP port checker for troubleshooting hosts and services you are authorized to test.

PortScope checks explicitly supplied hostnames/IPs and TCP ports, records connection latency, and can export results as JSON. It does not perform host discovery or scan port ranges by default.

## Requirements

- Python 3.11+
- No runtime dependencies

## Install

```bash
git clone https://github.com/6h7karchive/portscope.git
cd portscope
python -m pip install -e ".[dev]"
```

## Usage

Check a few ports on a host:

```bash
portscope example.com --ports 80,443,8443
```

Set a connection timeout and export JSON:

```bash
portscope 192.0.2.10 --ports 22,80,443 --timeout 1.5 --json results.json
```

Use only against systems you own or are authorized to test. PortScope makes TCP connection attempts; a result can be affected by firewalls, routing, and service availability.

## Development

```bash
python -m pytest
ruff check .
```

## Output

Each result includes the target, port, status, and elapsed milliseconds when available. JSON output is a list of result objects.

## License

MIT. See [LICENSE](LICENSE).
