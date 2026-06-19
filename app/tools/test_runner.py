import subprocess
import sys
import os
import re
from pathlib import Path

# use project directory for temp files to avoid Windows path issues
TEMP_DIR = Path("tests/temp")
TEMP_DIR.mkdir(exist_ok=True)


def run_tests(test_code: str, source_code: str = "") -> dict:
    """
    runs pytest on the provided test code.
    returns structured results with pass/fail counts.
    """
    full_code = ""
    if source_code:
        full_code += source_code + "\n\n"
    full_code += test_code

    tmp_path = TEMP_DIR / "test_temp.py"

    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(full_code)

        result = subprocess.run(
            [
                sys.executable, "-m", "pytest",
                str(tmp_path),
                "-v",
                "--tb=short",
                "--no-header",
                "-p", "no:cacheprovider",
            ],
            capture_output=True,
            text=True,
            timeout=120,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        )

        output = result.stdout + result.stderr

        passed = len(re.findall(r"PASSED", output))
        failed = len(re.findall(r"FAILED", output))
        errors = len(re.findall(r"ERROR", output))

        failures = []
        failure_blocks = re.findall(
            r"FAILED.*?(?=FAILED|PASSED|ERROR|=====|$)",
            output,
            re.DOTALL
        )
        for block in failure_blocks[:3]:
            failures.append(block.strip())

        success = result.returncode == 0

        return {
            "success": success,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "total": passed + failed + errors,
            "failures": failures,
            "raw_output": output[:2000],
            "summary": format_test_summary(passed, failed, errors, failures)
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "tests timed out after 120 seconds",
            "summary": "Test run failed: timeout"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "summary": f"Test run failed: {e}"
        }
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def format_test_summary(passed, failed, errors, failures) -> str:
    lines = []
    total = passed + failed + errors
    lines.append(f"Test results: {passed}/{total} passed")

    if failed == 0 and errors == 0:
        lines.append("All tests passed!")
        return "\n".join(lines)

    if failures:
        lines.append("\nFailure details:")
        for f in failures:
            lines.append(f"  {f[:200]}")

    return "\n".join(lines)


if __name__ == "__main__":
    source = """
def add(a, b):
    return a + b
"""

    tests = """
import unittest

class TestAdd(unittest.TestCase):
    def test_add_positive(self):
        self.assertEqual(add(2, 3), 5)

    def test_add_negative(self):
        self.assertEqual(add(-1, -1), -2)

    def test_add_wrong(self):
        self.assertEqual(add(2, 2), 5)  # this should fail

if __name__ == "__main__":
    unittest.main()
"""

    print("testing test runner...")
    result = run_tests(tests, source)
    print(result["summary"])
    print("\nraw output:")
    print(result["raw_output"])