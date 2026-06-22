"""
Gated pipeline runner: validate first, analyze only on clean data.

Runs `validate_data.py --strict`; if every data-quality test passes it proceeds
to `analyze.py`. If any validation test fails, it stops and the analysis is NOT
run (the failing report is still written to the "Data Quality" tab).

Any extra arguments are forwarded to analyze.py, e.g.:
    python run_analysis.py --min-support 0.01 --min-confidence 0.2 --top 30
"""

import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable  # the venv interpreter running this script


def run(script, *extra):
    print(f"\n{'=' * 70}\n>> {script} {' '.join(extra)}\n{'=' * 70}", flush=True)
    return subprocess.run([PY, os.path.join(BASE_DIR, script), *extra]).returncode


def main():
    analyze_args = sys.argv[1:]  # forward CLI args to analyze.py

    rc = run("validate_data.py", "--strict")
    if rc != 0:
        print("\nValidation FAILED — see the 'Data Quality' tab. "
              "Analysis was skipped.")
        sys.exit(rc)

    print("\nValidation passed — proceeding to analysis.")
    rc = run("analyze.py", *analyze_args)
    sys.exit(rc)


if __name__ == "__main__":
    main()
