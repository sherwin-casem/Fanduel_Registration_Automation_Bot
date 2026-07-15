import argparse
import ast
import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path

from fundrel_automation.core.paths import (
    ACCOUNTS_PATH,
    BASE_DIR,
    ENV_PATH,
    IMAGE_TARGETS_DIR,
    SETTINGS_PATH,
)
from fundrel_automation.core.accounts import load_accounts, validate_account
from fundrel_automation.core.config import load_settings
from fundrel_automation.core.routing import select_url_and_proxy


EXAMPLE_ACCOUNTS_PATH = BASE_DIR / "data" / "accounts.example.json"
EXAMPLE_ENV_PATH = BASE_DIR / ".env.example"
EXAMPLE_SETTINGS_PATH = BASE_DIR / "data" / "settings.example.json"


def copy_if_missing(source, target):
    if target.exists():
        return False
    shutil.copyfile(source, target)
    return True


def env_lines_from_settings(settings):
    proxies = []
    for proxy in settings.get("proxies", []):
        host = str(proxy.get("host", "")).strip()
        port = str(proxy.get("port", "")).strip()
        user = str(proxy.get("user", "")).strip()
        password = str(proxy.get("pass", "")).strip()
        if host and port and user and password:
            proxies.append(f"{host}:{port}:{user}:{password}")

    first_proxy = settings.get("proxies", [{}])[0] if settings.get("proxies") else {}
    edge_path = settings.get("edge_path", "")

    return [
        "# Local developer overrides. This file is ignored by git.",
        f"FUNDREL_EDGE_PATH={edge_path}",
        f"FUNDREL_PROXIES={','.join(proxies)}",
        f"FUNDREL_PROXY_SERVER=http://{first_proxy.get('host', 'proxy.example.com')}:{first_proxy.get('port', '10001')}",
        f"FUNDREL_PROXY_HOST={first_proxy.get('host', 'proxy.example.com')}",
        f"FUNDREL_PROXY_PORT={first_proxy.get('port', '10001')}",
        f"FUNDREL_PROXY_USER={first_proxy.get('user', 'proxy-user')}",
        f"FUNDREL_PROXY_PASS={first_proxy.get('pass', 'proxy-password')}",
        "FUNDREL_DEMO_URL=https://example.com",
        "FUNDREL_DEMO_EMAIL=person@example.com",
        "FUNDREL_DEMO_PASSWORD=example-password",
        "",
    ]


def init_dev(_args):
    created = []
    for source, target in (
        (EXAMPLE_ENV_PATH, ENV_PATH),
        (EXAMPLE_SETTINGS_PATH, SETTINGS_PATH),
        (EXAMPLE_ACCOUNTS_PATH, ACCOUNTS_PATH),
    ):
        if copy_if_missing(source, target):
            created.append(target.name)

    if created:
        print("Created: " + ", ".join(created))
    else:
        print("Local files already exist.")

    return 0


def sync_env(_args):
    if not SETTINGS_PATH.exists():
        print("data/settings.json is missing. Run `python dev.py init` first.")
        return 1

    settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    ENV_PATH.write_text("\n".join(env_lines_from_settings(settings)), encoding="utf-8")

    proxy_count = len(settings.get("proxies", []))
    print(f"Updated .env from data/settings.json ({proxy_count} proxies).")
    return 0


def syntax_check(_args):
    for path in BASE_DIR.rglob("*.py"):
        ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    print("Syntax OK")
    return 0


def run_tests(_args):
    result = subprocess.run(
        [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests"],
        cwd=BASE_DIR,
        text=True,
        capture_output=True,
    )
    output = result.stdout + result.stderr
    if output:
        print(output, end="")
    return result.returncode


def doctor(_args):
    checks = []
    checks.append(("data/settings.json", SETTINGS_PATH.exists()))
    checks.append(("data/accounts.json", ACCOUNTS_PATH.exists()))
    checks.append((".env", ENV_PATH.exists()))
    checks.append(("assets/image_targets", IMAGE_TARGETS_DIR.exists()))
    checks.append(("image target PNGs", len(list(IMAGE_TARGETS_DIR.glob("*.png"))) > 0))

    for name, ok in checks:
        print(f"{'OK' if ok else 'MISSING'}  {name}")

    return 0 if all(ok for _, ok in checks) else 1


def smoke(_args):
    import automate2
    import ui  # noqa: F401 - import smoke test for the UI module

    settings = load_settings()
    accounts = load_accounts()
    edge_path = Path(settings.get("edge_path", ""))
    image_count = len(list(IMAGE_TARGETS_DIR.glob("*.png")))

    checks = [
        ("automation module imports", True),
        ("ui module imports", True),
        ("data/settings.json has proxies", len(settings.get("proxies", [])) > 0),
        ("data/accounts.json has accounts", len(accounts) > 0),
        ("Edge path exists", edge_path.exists()),
        ("image target PNGs exist", image_count > 0),
    ]

    if accounts:
        merged = {**automate2.DEFAULT_CONFIG, **accounts[0]}
        is_valid, reason = validate_account(merged)
        checks.append(("first account validates", is_valid))
        if not is_valid:
            print(f"First account validation reason: {reason}")

    if accounts:
        url, proxy, wait = select_url_and_proxy(copy.deepcopy(settings), accounts[0])
        checks.append(("routing returns homepage URL", bool(url)))
        checks.append(("routing returns proxy", proxy is not None))
        checks.append(("routing wait is numeric", isinstance(wait, (int, float))))

    for name, ok in checks:
        print(f"{'OK' if ok else 'FAIL'}  {name}")

    return 0 if all(ok for _, ok in checks) else 1


def check(args):
    for command in (syntax_check, run_tests, doctor):
        result = command(args)
        if result:
            return result
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description="Developer helper commands.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Create local .env/settings/accounts files if missing.").set_defaults(func=init_dev)
    subparsers.add_parser("syntax", help="Parse all Python files.").set_defaults(func=syntax_check)
    subparsers.add_parser("test", help="Run unit tests.").set_defaults(func=run_tests)
    subparsers.add_parser("doctor", help="Check local runtime files and assets.").set_defaults(func=doctor)
    subparsers.add_parser("smoke", help="Run non-invasive bot readiness checks.").set_defaults(func=smoke)
    subparsers.add_parser("sync-env", help="Rebuild local .env from data/settings.json.").set_defaults(func=sync_env)
    subparsers.add_parser("check", help="Run syntax, tests, and doctor.").set_defaults(func=check)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
