"""
Scanner wrapper tests — no subprocess, no DB, no Docker. Mocks
app.scanners.utils.run_subprocess (or, for the shell-vs-exec regression
guard, asyncio.create_subprocess_exec/shell directly) at the point each
scanner module imported it, and checks the constructed argv plus the
status classification for timeout/no_binary/malformed-output cases.
"""
import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from app.scanners.utils import normalize_target, run_subprocess


# --- run_subprocess: the shared no_binary/timeout/failed/success classifier ---

def test_run_subprocess_uses_exec_not_shell():
    with patch("asyncio.create_subprocess_exec", new=AsyncMock(side_effect=FileNotFoundError())) as mock_exec, \
         patch("asyncio.create_subprocess_shell") as mock_shell:
        asyncio.run(run_subprocess(["/bin/echo", "hi"]))
    mock_exec.assert_awaited_once()
    mock_shell.assert_not_called()


def test_run_subprocess_no_binary():
    with patch("asyncio.create_subprocess_exec", new=AsyncMock(side_effect=FileNotFoundError())):
        _, _, status = asyncio.run(run_subprocess(["/no/such/binary"]))
    assert status["status"] == "no_binary"


def test_run_subprocess_timeout():
    proc = AsyncMock()
    proc.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
    proc.kill = lambda: None
    with patch("asyncio.create_subprocess_exec", new=AsyncMock(return_value=proc)), \
         patch("asyncio.wait_for", new=AsyncMock(side_effect=asyncio.TimeoutError())):
        _, _, status = asyncio.run(run_subprocess(["/bin/sleep", "999"], timeout=1))
    assert status["status"] == "timeout"


def test_run_subprocess_nonzero_exit():
    proc = AsyncMock()
    proc.returncode = 1
    proc.communicate = AsyncMock(return_value=(b"", b"boom"))
    with patch("asyncio.create_subprocess_exec", new=AsyncMock(return_value=proc)):
        _, _, status = asyncio.run(run_subprocess(["/bin/false"]))
    assert status["status"] == "failed"
    assert "boom" in status["detail"]


def test_run_subprocess_success():
    proc = AsyncMock()
    proc.returncode = 0
    proc.communicate = AsyncMock(return_value=(b"ok\n", b""))
    with patch("asyncio.create_subprocess_exec", new=AsyncMock(return_value=proc)):
        stdout, _, status = asyncio.run(run_subprocess(["/bin/echo", "ok"]))
    assert status == {"status": "success", "detail": None}
    assert stdout.strip() == "ok"


# --- normalize_target: consistent across every scanner ---

@pytest.mark.parametrize("raw,expected", [
    ("example.com", "example.com"),
    ("EXAMPLE.com:8080", "example.com"),
    ("example.com/path", "example.com"),
    ("http://Example.com/path?x=1", "example.com"),
    ("example.com.", "example.com"),
    ("juice-shop", "juice-shop"),
    ("192.168.1.1", "192.168.1.1"),
])
def test_normalize_target(raw, expected):
    assert normalize_target(raw) == expected


# --- argv construction: every scanner passes a list, never a shell string ---

def test_subfinder_argv():
    import app.scanners.subfinder as subfinder

    captured = {}

    async def fake_run_subprocess(command, timeout=300, input_bytes=None):
        captured["command"] = command
        return "", "", {"status": "success", "detail": None}

    with patch.object(subfinder, "run_subprocess", fake_run_subprocess), \
         patch.object(subfinder, "_is_wildcard_domain", return_value=False):
        asyncio.run(subfinder.run("EXAMPLE.com"))

    assert isinstance(captured["command"], list)
    assert captured["command"] == ["/usr/local/bin/subfinder", "-d", "example.com", "-silent", "-all"]


def test_httpx_argv_and_stdin():
    import app.scanners.httpx as httpx_mod

    captured = {}

    async def fake_run_subprocess(command, timeout=300, input_bytes=None):
        captured["command"] = command
        captured["input_bytes"] = input_bytes
        return "", "", {"status": "success", "detail": None}

    with patch.object(httpx_mod, "run_subprocess", fake_run_subprocess):
        asyncio.run(httpx_mod.run(["example.com", "Sub.example.com"]))

    assert isinstance(captured["command"], list)
    assert captured["command"][0] == "/usr/local/bin/httpx"
    assert "-tech-detect" in captured["command"]
    stdin_urls = captured["input_bytes"].decode().split("\n")
    # Each normalized target expands to its default scheme URLs plus the
    # common non-standard web ports (httpx's own "-ports" flag is broken in
    # the pinned binary, see httpx.py's EXTRA_PORTS comment).
    assert "http://example.com" in stdin_urls
    assert "https://example.com" in stdin_urls
    assert "http://example.com:3000" in stdin_urls
    assert "http://sub.example.com:3000" in stdin_urls


# --- outdated client-side tech detection (min_secure_version vs. httpx's tech-detect) ---

def test_detect_outdated_tech_flags_old_jquery():
    import app.scanners.httpx as httpx_mod
    # jquery.json's min_secure_version is "3.5.0" — real library data, not a mock.
    assert httpx_mod._detect_outdated_tech(["jQuery:3.4.1"]) is True


def test_detect_outdated_tech_does_not_flag_current_jquery():
    import app.scanners.httpx as httpx_mod
    assert httpx_mod._detect_outdated_tech(["jQuery:3.6.0"]) is False


def test_detect_outdated_tech_ignores_unknown_tech():
    import app.scanners.httpx as httpx_mod
    assert httpx_mod._detect_outdated_tech(["SomeObscureLib:1.0.0"]) is False


def test_detect_outdated_tech_handles_empty_list():
    import app.scanners.httpx as httpx_mod
    assert httpx_mod._detect_outdated_tech([]) is False


def test_nmap_argv():
    import app.scanners.nmap as nmap_mod

    captured = {}

    async def fake_run_subprocess(command, timeout=300, input_bytes=None):
        captured["command"] = command
        return "", "", {"status": "success", "detail": None}

    with patch.object(nmap_mod, "run_subprocess", fake_run_subprocess):
        asyncio.run(nmap_mod.run(["example.com", "sub.example.com"]))

    assert isinstance(captured["command"], list)
    assert captured["command"] == [
        "/usr/bin/nmap", "-sV", "--script=default,ssh-auth-methods,banner,redis-info",
        "-T4", "--open", "-oX", "-", "example.com", "sub.example.com",
    ]


def test_nuclei_argv():
    import app.scanners.nuclei as nuclei_mod

    captured = {}

    async def fake_run_subprocess(command, timeout=300, input_bytes=None):
        captured["command"] = command
        return "", "", {"status": "success", "detail": None}

    with patch.object(nuclei_mod, "run_subprocess", fake_run_subprocess):
        asyncio.run(nuclei_mod.run(["example.com", "sub.example.com"]))

    command = captured["command"]
    assert isinstance(command, list)
    assert command[0] == "/usr/local/bin/nuclei"
    assert command.count("-u") == 2
    assert "example.com" in command
    assert "sub.example.com" in command


# --- error classification propagates through to each scanner's return value ---

def test_subfinder_propagates_timeout_status():
    import app.scanners.subfinder as subfinder

    async def fake_run_subprocess(command, timeout=300, input_bytes=None):
        return "", "", {"status": "timeout", "detail": "exceeded 300s"}

    with patch.object(subfinder, "run_subprocess", fake_run_subprocess):
        findings, status = asyncio.run(subfinder.run("example.com"))

    assert findings == []
    assert status == {"status": "timeout", "detail": "exceeded 300s"}


def test_nmap_propagates_no_binary_status():
    import app.scanners.nmap as nmap_mod

    async def fake_run_subprocess(command, timeout=300, input_bytes=None):
        return "", "", {"status": "no_binary", "detail": "/usr/bin/nmap not found"}

    with patch.object(nmap_mod, "run_subprocess", fake_run_subprocess):
        findings, status = asyncio.run(nmap_mod.run(["example.com"]))

    assert findings == []
    assert status["status"] == "no_binary"


def test_nmap_malformed_xml_is_a_distinct_failed_status():
    import app.scanners.nmap as nmap_mod

    async def fake_run_subprocess(command, timeout=300, input_bytes=None):
        return "<not><valid xml", "", {"status": "success", "detail": None}

    with patch.object(nmap_mod, "run_subprocess", fake_run_subprocess):
        findings, status = asyncio.run(nmap_mod.run(["example.com"]))

    assert findings == []
    assert status["status"] == "failed"
    assert "parse" in status["detail"].lower()


@pytest.mark.parametrize("scanner_name, module_path", [
    ("httpx", "app.scanners.httpx"),
    ("nuclei", "app.scanners.nuclei"),
])
def test_all_malformed_lines_is_a_distinct_failed_status_not_empty_success(scanner_name, module_path):
    import importlib
    mod = importlib.import_module(module_path)

    async def fake_run_subprocess(command, timeout=300, input_bytes=None):
        return "not json\nalso not json\n", "", {"status": "success", "detail": None}

    targets = ["example.com"]
    with patch.object(mod, "run_subprocess", fake_run_subprocess):
        findings, status = asyncio.run(mod.run(targets))

    assert findings == []
    assert status["status"] == "failed"
    assert "parse" in status["detail"].lower()


@pytest.mark.parametrize("module_path", ["app.scanners.httpx", "app.scanners.nuclei"])
def test_genuinely_empty_output_is_success_not_failed(module_path):
    """Distinguishes "tool ran fine, found nothing" from the malformed-output
    case above — both produce zero findings, but only one is a real failure."""
    import importlib
    mod = importlib.import_module(module_path)

    async def fake_run_subprocess(command, timeout=300, input_bytes=None):
        return "", "", {"status": "success", "detail": None}

    with patch.object(mod, "run_subprocess", fake_run_subprocess):
        findings, status = asyncio.run(mod.run(["example.com"]))

    assert findings == []
    assert status == {"status": "success", "detail": None}
