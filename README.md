# LLM Metadata Scraper

Official README for the LLM Metadata Scraper project.

This repository contains a Scrapy-based scraper that extracts metadata from model pages (Kaggle, NVIDIA, etc.). It provides an interactive menu and command-line entry points to run individual spiders or all spiders in sequence.

## Project layout

- `scrapy_project/` — main Scrapy project code and entry scripts
  - `main.py` — interactive CLI and application entrypoint
  - `run.py` — simple wrapper to run a single Scrapy spider
  - `requirements.txt` — Python dependencies
  - `my_scraper/` — scraper package (spiders, extractors, selectors, utils, etc.)
- `output/` — example output location used by spiders
- `schema/` — SQL schemas for output databases

## Supported platforms

This README describes setup for Windows (PowerShell). The same steps apply on macOS / Linux with small path/activation differences (use `source .venv/bin/activate`).

## Quick start (Windows PowerShell)

Open PowerShell in the repository root:

```powershell
# Change to repo root directory first (example path)
cd "c:\Users\orste\Downloads\llm_metadata_scraper-feat-parallel_run\llm_metadata_scraper-feat-parallel_run"
```

1) Create a virtual environment (recommended name: `.venv`):

```powershell
# If 'python' is on PATH
python -m venv .venv

# Or using the Windows Python launcher
py -3 -m venv .venv
```

2) Activate the virtual environment:

```powershell
# Activate for PowerShell
.\.venv\Scripts\Activate.ps1
```

If you see an ExecutionPolicy error, run a temporary process-scope bypass:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Or use the cmd-style activate from PowerShell (does not require changing ExecutionPolicy):

```powershell
cmd /c ".venv\Scripts\activate.bat"
```

3) Upgrade pip and install dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r scrapy_project\requirements.txt
```

# LLM Metadata Scraper

Official README for the LLM Metadata Scraper project.

This repository contains a Scrapy-based scraper that extracts metadata from model pages (Kaggle, NVIDIA, etc.). It provides an interactive menu and command-line entry points to run individual spiders or all spiders in sequence.

## Project layout

- `scrapy_project/` — main Scrapy project code and entry scripts
  - `main.py` — interactive CLI and application entrypoint
  - `run.py` — simple wrapper to run a single Scrapy spider
  - `requirements.txt` — Python dependencies
  - `my_scraper/` — scraper package (spiders, extractors, selectors, utils, etc.)
- `output/` — example output location used by spiders
- `schema/` — SQL schemas for output databases

## Supported platforms

This README includes setup instructions for Windows (PowerShell) and macOS / Linux. Use the macOS/Linux instructions when working in a POSIX shell (bash, zsh, fish, etc.).

---

## Quick start (Windows PowerShell)

Open PowerShell in the repository root:

```powershell
# Change to repo root directory first (example path)
cd "c:\Users\orste\Downloads\reusable_scraper_project\reusable_scraper_project"
```

1. Create a virtual environment (recommended name: `.venv`):

```powershell
# If 'python' is on PATH
python -m venv .venv

# Or using the Windows Python launcher
py -3 -m venv .venv
```

2. Activate the virtual environment:

```powershell
# Activate for PowerShell
.\.venv\Scripts\Activate.ps1
```

If you see an ExecutionPolicy error, run a temporary process-scope bypass:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Or use the cmd-style activate from PowerShell (does not require changing ExecutionPolicy):

```powershell
cmd /c ".venv\Scripts\activate.bat"
```

3. Upgrade pip and install dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r scrapy_project\requirements.txt
```

4. Verify installation:

```powershell
where python
python -c "import sys; print(sys.executable); import pkgutil; print('scrapy' if pkgutil.find_loader('scrapy') else 'scrapy not found')"

# Or list installed packages
pip list
```

---

## Quick start (macOS / Linux)

Open a terminal in the repository root and run:

```bash
# Change to repo root (example)
cd "/path/to/llm_metadata_scraper-feat-parallel_run"

# Create venv (POSIX shells)
python3 -m venv .venv

# Activate
source .venv/bin/activate

# Upgrade pip and install requirements
python -m pip install --upgrade pip
pip install -r scrapy_project/requirements.txt

# Verify
which python
python -c "import sys; print(sys.executable); import pkgutil; print('scrapy' if pkgutil.find_loader('scrapy') else 'scrapy not found')"
```

Notes for macOS:
- If you have both Python 2 and Python 3, prefer `python3 -m venv .venv`.
- On macOS, you may need to install developer tools or use Homebrew to manage Python: `brew install python`.

Selenium / WebDriver notes:
- Some spiders use Selenium for JavaScript-rendered pages. Install a matching WebDriver for your browser (e.g., ChromeDriver for Google Chrome, geckodriver for Firefox) and ensure it's on your PATH.

---

## Running the scraper

A. Interactive menu (recommended for exploring spiders):

Windows PowerShell:

```powershell
python scrapy_project\main.py
```

macOS / Linux:

```bash
python scrapy_project/main.py
```

Options supported by `main.py`:

- `--list` or `-l` — list all detected spiders
- `--spider <name>` or `-s <name>` — run a specific spider
- `--args key=value,...` or `-a` — pass spider args
- `--all` — run all spiders in sequence

Examples:

```powershell
# List spiders (Windows)
python scrapy_project\main.py --list

# Run a spider with args (Windows)
python scrapy_project\main.py --spider kaggle_links --args max_pages=10

# Run all spiders (Windows)
python scrapy_project\main.py --all
```

```bash
# List spiders (macOS / Linux)
python scrapy_project/main.py --list

# Run a spider with args (macOS / Linux)
python scrapy_project/main.py --spider kaggle_links --args max_pages=10

# Run all spiders (macOS / Linux)
python scrapy_project/main.py --all
```

B. Run a single spider with the lightweight wrapper `run.py`:

Windows:

```powershell
# Run by spider name (Windows)
python scrapy_project\run.py kaggle_links

# With Scrapy -a style arguments (Windows)
python scrapy_project\run.py kaggle_links -a max_pages=10
```

macOS / Linux:

```bash
# Run by spider name (macOS / Linux)
python scrapy_project/run.py kaggle_links

# With Scrapy -a style arguments (macOS / Linux)
python scrapy_project/run.py kaggle_links -a max_pages=10
```

`run.py` changes to the project directory then calls Scrapy's command-line API.

## Configuration

- `my_scraper/scraper_config.json` — optional runtime config managed by the Settings Menu. Use the interactive Settings Menu from `main.py` -> "Settings Menu" to configure.

## Output

By default spiders write files to the `output/` directory. Check each spider's module for exact file names and formats.

## Troubleshooting

- ExecutionPolicy prevents `Activate.ps1`: use the process-scope bypass shown above or activate using the `.bat` script via `cmd /c`.
- If Scrapy commands fail: ensure the virtualenv is active and `scrapy` appears in `pip list`.
- Selenium issues: verify a compatible WebDriver is available (e.g., ChromeDriver for Chrome). Some spiders may use Selenium for JS rendering; check `my_scraper/extractors/selenium_utils.py` for details.

## Developer notes

- To add a spider, place a spider module in `my_scraper/spiders/` and ensure `SpiderManager` detects it.
- Use `python -m pip install -e .` if converting to an installable package for development, or add an editable install for local imports.

## License & attribution

This project is provided as-is. Refer to repository metadata for any license details.
