"""Run pytest with a fresh workspace-local temp path on every invocation.

Pytest deletes an existing --basetemp directory at startup. A unique name avoids
permission errors when an earlier run was created by another Windows account.
"""

import subprocess
import shutil
import sys
import uuid
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent
    base_temp = root / f".pytest_run_{uuid.uuid4().hex}"
    project_python = root / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    interpreter = project_python if project_python.is_file() else Path(sys.executable)
    print(f"Running tests with {interpreter}", flush=True)
    code = subprocess.call(
        [str(interpreter), "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--basetemp={base_temp}", *sys.argv[1:]],
        cwd=root,
    )
    # Remove only this invocation's successful, workspace-local test artifacts.
    # Failed runs remain available for diagnosis.
    if code == 0 and base_temp.exists():
        assert base_temp.resolve().parent == root and base_temp.name.startswith('.pytest_run_')
        try:
            shutil.rmtree(base_temp)
        except OSError as exc:
            print(f'Tests passed; temporary files could not be removed: {exc}')
    return code


if __name__ == "__main__":
    raise SystemExit(main())
