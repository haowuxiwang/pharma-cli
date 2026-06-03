# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**stats-cli** — AI-friendly statistical analysis CLI for manufacturing, powered by R. Python handles CLI, data loading/cleaning, chart generation (Plotly), and reports (Jinja2). R handles all statistical computation via 24 scripts called through subprocess with JSON I/O.

## Commands

```bash
# Install
pip install -e .

# Run tests
python -m pytest tests/ -v

# Run tests with coverage
python -m pytest tests/ -v --cov=cli --cov-report=term-missing

# Run a single test file
python -m pytest tests/test_validators.py -v

# Run a single test
python -m pytest tests/test_validators.py::TestValidators::test_name -v

# Run the CLI
stats-cli <command> [options]

# Dev mode
python -m cli <command> [options]
```

## Architecture

### Data Flow

```
CLI args/file/stdin
    → load_data() (cli/commands/utils.py)
    → clean_values() (cli/data_cleaner.py)  # removes NaN, Inf, non-numeric
    → R script via subprocess (cli/r_engine.py)
    → JSON output on stdout
```

### R Engine (`cli/r_engine.py`)

Finds Rscript via `RSCRIPT_PATH` env var, common Windows paths, or system PATH. Writes R script to temp file, passes data as JSON via stdin, parses JSON output from stdout. Returns structured error dicts (`error_type`, `message`, `suggestion`) on failure.

### Command Pattern

Every command in `cli/commands/<name>.py` follows the same template:
1. Click command definition with options
2. `load_data()` to read file/stdin
3. `run_r_file("script.R", data)` to execute R script
4. Optional chart/report generation based on `--plot` / `--interactive` / `--report` flags
5. `output(result)` to print JSON

### Adding a New Command

1. Create `cli/commands/<name>.py` with a Click command
2. Create `r_scripts/<name>.R` — read JSON from stdin, write JSON to stdout
3. Add import in `cli/commands/__init__.py` and `cli/main.py` (`main.add_command(...)`)

## Output Format

All commands output JSON with a standard wrapper:
```json
{
  "status": "success|error",
  "version": "0.4.0",
  "timestamp": "...",
  "data": { ... }
}
```

## Chart Modes

- `--plot`: Base64-encoded PNG (via R)
- `--interactive`: Interactive Plotly HTML files
- `--report`: Full HTML reports via Jinja2 templates (`cli/templates/`)
