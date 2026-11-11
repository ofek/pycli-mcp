# SPDX-FileCopyrightText: 2025-present Ofek Lev <oss@ofek.dev>
# SPDX-License-Identifier: MIT
from __future__ import annotations

from click.testing import CliRunner

from pycli_mcp.cli import pycli_mcp


def test_invalid_include_pattern_raises_value_error() -> None:
    result = CliRunner().invoke(pycli_mcp, ["click:command", "--include", "["])
    assert result.exit_code == 1
    assert isinstance(result.exception, ValueError)
    assert "Invalid include pattern" in str(result.exception)


def test_invalid_exclude_pattern_raises_value_error() -> None:
    result = CliRunner().invoke(pycli_mcp, ["click:command", "--exclude", "("])
    assert result.exit_code == 1
    assert isinstance(result.exception, ValueError)
    assert "Invalid exclude pattern" in str(result.exception)
