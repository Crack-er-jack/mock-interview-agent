"""Subprocess-based Python code sandbox with safety limits."""

import subprocess
import re
import config


# Imports that are blocked for safety
BLOCKED_IMPORTS = [
    "os", "sys", "subprocess", "socket", "requests", "urllib",
    "shutil", "pathlib", "importlib", "ctypes", "signal",
    "multiprocessing", "threading",
]


def _check_dangerous_imports(code: str) -> str | None:
    """Return a warning message if dangerous imports are detected, else None."""
    for mod in BLOCKED_IMPORTS:
        # Match: import os, from os import ..., __import__("os")
        patterns = [
            rf"\bimport\s+{mod}\b",
            rf"\bfrom\s+{mod}\b",
            rf'__import__\s*\(\s*["\']({mod})["\']',
        ]
        for pat in patterns:
            if re.search(pat, code):
                return f"Blocked: importing '{mod}' is not allowed in the sandbox."
    return None


def _build_test_runner(user_code: str, test_cases: list[dict]) -> str:
    """
    Build the full script: user code + hidden assertions.

    Each test_case dict should have:
      - "input": the argument(s) to pass to `solution()`
      - "expected": the expected return value
    """
    lines = [user_code, "", "# ── Hidden test cases ──", "_passed = 0", "_failed = 0"]

    for i, tc in enumerate(test_cases):
        inp = repr(tc["input"])
        exp = repr(tc["expected"])
        lines.append(f"try:")
        lines.append(f"    _result = solution({inp})")
        lines.append(f"    assert _result == {exp}, f'Test {i+1}: got {{_result}}, expected {exp}'")
        lines.append(f"    _passed += 1")
        lines.append(f"except AssertionError as e:")
        lines.append(f"    _failed += 1")
        lines.append(f"    print(f'FAIL: {{e}}')")
        lines.append(f"except Exception as e:")
        lines.append(f"    _failed += 1")
        lines.append(f"    print(f'ERROR in test {i+1}: {{e}}')")

    lines.append(f"print(f'Results: {{_passed}} passed, {{_failed}} failed out of {len(test_cases)}')")

    return "\n".join(lines)


def execute_code(
    code: str,
    test_cases: list[dict] | None = None,
) -> dict:
    """
    Execute Python code in a subprocess sandbox.

    Returns dict with: stdout, stderr, passed, failed, total, timed_out
    """
    # Check code length
    if len(code) > config.MAX_CODE_LENGTH:
        return {
            "stdout": "",
            "stderr": f"Code exceeds maximum length of {config.MAX_CODE_LENGTH} characters.",
            "passed": 0,
            "failed": 0,
            "total": 0,
            "timed_out": False,
        }

    # Check dangerous imports
    warning = _check_dangerous_imports(code)
    if warning:
        return {
            "stdout": "",
            "stderr": warning,
            "passed": 0,
            "failed": 0,
            "total": 0,
            "timed_out": False,
        }

    # Build script
    total = 0
    if test_cases:
        total = len(test_cases)
        script = _build_test_runner(code, test_cases)
    else:
        script = code

    # Run in subprocess
    try:
        result = subprocess.run(
            ["python", "-c", script],
            capture_output=True,
            text=True,
            timeout=config.SANDBOX_TIMEOUT,
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        # Parse pass/fail counts from output
        passed = 0
        failed = 0
        if test_cases:
            # Count FAIL lines
            failed = stdout.count("FAIL:") + stdout.count("ERROR in test")
            passed = total - failed

        return {
            "stdout": stdout,
            "stderr": stderr,
            "passed": passed,
            "failed": failed,
            "total": total,
            "timed_out": False,
        }

    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": f"Code execution timed out after {config.SANDBOX_TIMEOUT} seconds.",
            "passed": 0,
            "failed": 0,
            "total": total,
            "timed_out": True,
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": f"Execution error: {str(e)}",
            "passed": 0,
            "failed": 0,
            "total": total,
            "timed_out": False,
        }
