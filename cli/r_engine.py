"""R engine layer - calls Rscript and handles JSON I/O."""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

# R scripts directory
R_SCRIPTS_DIR = Path(__file__).parent.parent / "r_scripts"


def find_rscript() -> str:
    """Find Rscript executable.

    Search order:
    1. RSCRIPT_PATH environment variable
    2. Common installation paths (Windows)
    3. System PATH
    """
    import shutil

    # 1. Check environment variable
    env_path = os.environ.get("RSCRIPT_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path

    # 2. Check common Windows paths
    common_paths = [
        r"D:\R-4.6.0\bin\Rscript.exe",
        r"D:\R-4.5.0\bin\Rscript.exe",
        r"D:\R-4.4.0\bin\Rscript.exe",
        r"C:\Program Files\R\R-4.6.0\bin\Rscript.exe",
        r"C:\Program Files\R\R-4.5.0\bin\Rscript.exe",
        r"C:\Program Files\R\R-4.4.0\bin\Rscript.exe",
    ]
    for path in common_paths:
        if os.path.isfile(path):
            return path

    # 3. Try system PATH
    path = shutil.which("Rscript")
    if path:
        return path

    raise RuntimeError(
        "Rscript not found. Install R or set RSCRIPT_PATH environment variable.\n"
        "Download R from: https://cran.r-project.org/bin/windows/base/"
    )


def run_r_script(script: str, data: Optional[Dict[str, Any]] = None, timeout: int = 60) -> Dict[str, Any]:
    """
    Run an R script and return parsed JSON result.

    Args:
        script: R script code (must print JSON to stdout)
        data: Optional dict passed as JSON to R via stdin
        timeout: Timeout in seconds

    Returns:
        Parsed JSON result from R script, or structured error dict on failure
    """
    rscript = find_rscript()

    # Write script to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".R", delete=False, encoding="utf-8") as f:
        f.write(script)
        script_path = f.name

    try:
        input_json = json.dumps(data) if data else None
        result = subprocess.run(
            [rscript, script_path],
            input=input_json,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
        )
        if result.returncode != 0:
            return {
                "error": True,
                "error_type": "R_SCRIPT_ERROR",
                "message": result.stderr.strip() if result.stderr else "R script failed",
                "suggestion": "Check if required R packages are installed"
            }
        if not result.stdout.strip():
            return {
                "error": True,
                "error_type": "NO_OUTPUT",
                "message": "R script produced no output",
                "suggestion": "Check R script for print/cat statements"
            }
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        return {
            "error": True,
            "error_type": "TIMEOUT",
            "message": f"R script timed out after {timeout} seconds",
            "suggestion": "Try reducing data size or increasing timeout"
        }
    except Exception as e:
        return {
            "error": True,
            "error_type": "EXECUTION_ERROR",
            "message": str(e),
            "suggestion": "Check R installation and script syntax"
        }
    finally:
        os.unlink(script_path)


def run_r_file(script_name: str, data: Optional[Dict[str, Any]] = None, timeout: int = 60) -> Dict[str, Any]:
    """
    Run an R script file from the r_scripts directory.

    Args:
        script_name: Name of the R script file (e.g., "descriptive.R")
        data: Optional dict passed as JSON to R via stdin
        timeout: Timeout in seconds

    Returns:
        Parsed JSON result from R script, or structured error dict on failure
    """
    script_path = R_SCRIPTS_DIR / script_name
    if not script_path.exists():
        return {
            "error": True,
            "error_type": "SCRIPT_NOT_FOUND",
            "message": f"R script not found: {script_path}",
            "suggestion": f"Check that {script_name} exists in the r_scripts directory"
        }

    rscript = find_rscript()
    input_json = json.dumps(data) if data else None

    try:
        result = subprocess.run(
            [rscript, str(script_path)],
            input=input_json,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
        )
    except subprocess.TimeoutExpired:
        return {
            "error": True,
            "error_type": "TIMEOUT",
            "message": f"R script timed out after {timeout} seconds",
            "suggestion": "Try reducing data size or increasing timeout"
        }
    except Exception as e:
        return {
            "error": True,
            "error_type": "EXECUTION_ERROR",
            "message": str(e),
            "suggestion": "Check R installation and script syntax"
        }

    if result.returncode != 0:
        return {
            "error": True,
            "error_type": "R_SCRIPT_ERROR",
            "message": result.stderr.strip() if result.stderr else "R script failed with no error message",
            "suggestion": "Check if required R packages are installed (jsonlite, nortest, qcc, car)"
        }
    if not result.stdout.strip():
        return {
            "error": True,
            "error_type": "NO_OUTPUT",
            "message": "R script produced no output",
            "suggestion": "Check R script for print/cat statements"
        }

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        return {
            "error": True,
            "error_type": "JSON_PARSE_ERROR",
            "message": f"Failed to parse R script output as JSON: {e}",
            "suggestion": "Check R script output format"
        }
