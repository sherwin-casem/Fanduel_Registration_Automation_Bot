# FanDuel AutoBot Dashboard

## Overview
This desktop app manages account records, settings, and browser automation runs from a Tkinter UI. It supports importing accounts, configuring proxies, running pending accounts, and saving screenshots/results for each run.

## Features
- Full automation runner for account registration flow
- Tabs for Pending, Created, Failed, Skipped, Another Account, Service Unavailable, and Unable to Verify
- JSON, CSV, and Excel export
- Date filtering for run history
- Send failed/unverified accounts back to Pending
- Configurable proxies and Edge path
- Screenshot capture for completed/error runs

## Installation

1. Make sure Python 3.9+ is installed.
2. Clone or download this repository.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create local runtime files:
   ```bash
   python dev.py init
   ```

`data/accounts.json`, `data/settings.json`, and `.env` are local-only files and are ignored by git.

## How To Run

### Run The UI
```bash
python ui.py
```

### Run Automation From The Command Line
```bash
python automate2.py
```

You need a `data/accounts.json` file with account data. Use `data/accounts.example.json` as a template.

## Developer Commands

```bash
python dev.py init      # create local .env/settings/accounts files if missing
python dev.py doctor    # check local files and image target assets
python dev.py smoke     # run non-invasive bot readiness checks
python dev.py sync-env  # rebuild .env from local data/settings.json
python dev.py test      # run unit tests
python dev.py syntax    # parse all Python files
python dev.py check     # run syntax, tests, and doctor
```

## Logs

Terminal output and automation/UI logs are written to:

```text
runtime/logs/fundrel.log
```

The log file rotates automatically so it does not grow forever.

## Project Data

- `data/accounts.json`: local account data. Not committed.
- `data/settings.json`: local settings and proxies. Not committed.
- `.env`: local developer overrides. Not committed.
- `.env.example`: safe template for `.env`.
- Use `python dev.py sync-env` after editing settings in the UI if you want `.env` to mirror `data/settings.json`.
- `assets/image_targets`: PNG image targets used by PyAutoGUI recognition.
- `images_result`: dated result screenshots from automation runs. Not committed.
- `runtime`: temporary/local runtime artifacts. Not committed.

## Creating An EXE File

To package the app into a standalone Windows executable:

```bash
pyinstaller --onefile --windowed --name "FanDuel AutoBot" --add-data "assets/image_targets;assets/image_targets" ui.py
```

The executable will be created in `dist/`.

## Configuration

- Open Settings in the UI to configure Edge path and proxies.
- Keep image target files such as `email1.png` and `create_account.png` in `assets/image_targets`.
- Upload account data from JSON or Excel, or add accounts manually.

## Important Notes

- Do not touch the mouse or keyboard while automation is running.
- The bot has a failsafe: move the mouse to the top-left corner of the screen to stop immediately.
- Make sure Microsoft Edge is installed and the configured Edge path is correct.
