import subprocess
import tempfile
import os
import sys
import json


def run_linter(code: str) -> dict:
    """
    runs pylint on the provided code string.
    returns structured results with errors, warnings, and score.
    """
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        delete=False,
        encoding="utf-8"
    ) as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            [
                sys.executable, "-m", "pylint",
                tmp_path,
                "--output-format=json",
                "--disable=C0114,C0115,C0116",  # disable missing docstring warnings
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        issues = []
        if result.stdout.strip():
            try:
                raw_issues = json.loads(result.stdout)
                for issue in raw_issues:
                    issues.append({
                        "line": issue.get("line"),
                        "column": issue.get("column"),
                        "type": issue.get("type"),
                        "symbol": issue.get("symbol"),
                        "message": issue.get("message"),
                    })
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"Failed to parse pylint output: {e}",
                    "raw_output": result.stdout[:500],
                    "summary": "Linting failed: could not parse output"
                }

        # categorize by type
        errors = [i for i in issues if i["type"] == "error"]
        warnings = [i for i in issues if i["type"] == "warning"]
        refactors = [i for i in issues if i["type"] == "refactor"]
        conventions = [i for i in issues if i["type"] == "convention"]

        return {
            "success": True,
            "score": None,
            "total_issues": len(issues),
            "errors": errors,
            "warnings": warnings,
            "refactors": refactors,
            "conventions": conventions,
            "summary": format_lint_summary(errors, warnings, refactors, conventions)
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "linter timed out after 30 seconds",
            "summary": "Linting failed: timeout"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "summary": f"Linting failed: {e}"
        }
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def format_lint_summary(errors, warnings, refactors, conventions) -> str:
    """formats lint results into a readable string for the LLM"""
    lines = []

    if not errors and not warnings and not refactors and not conventions:
        lines.append("No issues found!")
        return "\n".join(lines)

    total = len(errors) + len(warnings) + len(refactors) + len(conventions)
    lines.append(f"Found {total} issue(s):")

    if errors:
        lines.append(f"\nErrors ({len(errors)}):")
        for e in errors:
            lines.append(f"  Line {e['line']}: [{e['symbol']}] {e['message']}")

    if warnings:
        lines.append(f"\nWarnings ({len(warnings)}):")
        for w in warnings:
            lines.append(f"  Line {w['line']}: [{w['symbol']}] {w['message']}")

    if refactors:
        lines.append(f"\nRefactor suggestions ({len(refactors)}):")
        for r in refactors:
            lines.append(f"  Line {r['line']}: [{r['symbol']}] {r['message']}")

    if conventions:
        lines.append(f"\nConventions ({len(conventions)}):")
        for c in conventions[:3]:
            lines.append(f"  Line {c['line']}: [{c['symbol']}] {c['message']}")
        if len(conventions) > 3:
            lines.append(f"  ... and {len(conventions) - 3} more")

    return "\n".join(lines)


if __name__ == "__main__":
    bad_code = """
def read_file(path):
    f = open(path)
    data = f.read()
    return data

x = undefined_variable
"""
    print("testing linter on bad code...")
    result = run_linter(bad_code)
    print(result["summary"])
    print(f"\nfull result errors: {result['errors']}")