# Windows uv troubleshooting

Use **PowerShell** in your project folder. Replace `3.12` with your required Python version.

## 1. Check that uv and Python run

```powershell
uv --version
uv run --no-project --isolated --python 3.12 python -c "import sys; print('Python works'); print(sys.version)"
```

The second command tests Python without your project's dependencies or existing `.venv`. It may download Python if needed.

If it prints **Python works**, test the project environment:

```powershell
uv run python -c "import sys; print('Project Python works'); print(sys.executable); print(sys.version)"
```

If both pass, run your script:

```powershell
uv run python hello-world.py
```

## 2. Match the failure to a cause

| What happens | Likely cause / next step |
|---|---|
| `uv` is not recognized | Install uv using the [Windows instructions](https://docs.astral.sh/uv/getting-started/installation/), then reopen PowerShell. |
| Wrong Python version | Select the version below. Plain `python` can still use a different installation from `PATH`. |
| `encodings` / `init_fs_encoding` error | Test for environment-variable overrides below. |
| Basic test passes; project startup fails | Check the error: `.venv` may be broken, or project dependency installation may have failed. |
| `No module named ...` after Python starts | Run `uv sync` for declared dependencies. If the package is missing from `pyproject.toml`, add its package name with `uv add`. |
| Download, proxy, or certificate error | Check the VM's network/proxy/certificate setup; this does not establish a Python runtime failure. |
| Script file cannot be found | Open the folder containing `hello-world.py`, or provide its full path. |

### Wrong version

```powershell
uv python pin 3.12
uv sync --python 3.12
```

Retry the project test. Leave out `--active` and `--no-sync` while switching versions.

### `encodings` startup error

If `.venv` exists, test while ignoring Python environment variables:

```powershell
.\.venv\Scripts\python.exe -E -c "print('Python works')"
```

If that succeeds, clear the overrides for this terminal and retry:

```powershell
Remove-Item Env:PYTHONHOME -ErrorAction SilentlyContinue
Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
uv run python hello-world.py
```

If this fixes it, remove or correct the offending entries in Windows **Environment Variables**, then reopen PowerShell. `encodings` ships with Python; do not install it with pip.

### Broken or copied `.venv`

If the basic test passes but `.venv` cannot start even with `-E`, rename `.venv` to an unused backup name, then rebuild it locally:

```powershell
uv sync --python 3.12
```

If the basic test also fails, save the full error before changing the installation.

References: [uv commands](https://docs.astral.sh/uv/reference/cli/), [Python environment and path settings](https://docs.python.org/3/library/sys_path_init.html).
