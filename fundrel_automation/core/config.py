import json
import re
from copy import deepcopy

from .env import load_env, split_env_list
from .paths import LEGACY_SETTINGS_PATH, SETTINGS_PATH

LEGACY_SETTING_KEYS = (
    "urls",
    "referrals",
    "referral_mode",
    "referral_state",
    "url_index",
    "proxy_index",
)

DEFAULT_SETTINGS = {
    "edge_path": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "proxies": [],
}


def _migrate_settings(settings):
    changed = False

    for key in LEGACY_SETTING_KEYS:
        if key in settings:
            del settings[key]
            changed = True

    settings.setdefault("proxies", [])
    settings.setdefault("edge_path", DEFAULT_SETTINGS["edge_path"])

    return settings, changed


def settings_from_env(env=None):
    env = env if env is not None else load_env()
    settings = deepcopy(DEFAULT_SETTINGS)

    edge_path = env.get("FUNDREL_EDGE_PATH")
    if edge_path:
        settings["edge_path"] = edge_path

    proxies = split_env_list(env.get("FUNDREL_PROXIES", ""))
    if proxies:
        settings["proxies"] = [_proxy_from_string(proxy) for proxy in proxies]

    return settings


def apply_env_defaults(settings, env=None):
    env_settings = settings_from_env(env)

    if settings.get("edge_path") == DEFAULT_SETTINGS["edge_path"]:
        settings["edge_path"] = env_settings["edge_path"]
    if not settings.get("proxies"):
        settings["proxies"] = env_settings["proxies"]

    return settings


def load_settings(path=SETTINGS_PATH):
    if path == SETTINGS_PATH and not path.exists() and LEGACY_SETTINGS_PATH.exists():
        path = LEGACY_SETTINGS_PATH

    if not path.exists():
        settings = settings_from_env()
        save_settings(settings, SETTINGS_PATH)
        return settings

    with path.open("r", encoding="utf-8") as f:
        settings = json.load(f)

    settings, changed = _migrate_settings(settings)
    settings = apply_env_defaults(settings)
    if changed:
        save_settings(settings, path)

    return settings


def save_settings(settings, path=SETTINGS_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)


def _proxy_from_string(value):
    parts = value.split(":", 3)
    if len(parts) < 4:
        raise ValueError(f"Invalid proxy format:\n{value}\nExpected host:port:user:pass")

    return {
        "host": parts[0].strip(),
        "port": parts[1].strip(),
        "user": parts[2].strip(),
        "pass": parts[3].strip(),
        "last_use": 0,
    }


def parse_proxies(raw):
    raw = raw.strip()
    proxies = []
    if not raw:
        return proxies

    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, list):
            raise ValueError("Proxies JSON must be a list.")

        for item in parsed:
            if isinstance(item, dict):
                proxies.append(item)
            elif isinstance(item, str):
                proxies.append(_proxy_from_string(item))
        return proxies
    except Exception as exc:
        if "{" in raw:
            raise ValueError(
                "Proxies format is invalid. If mixing JSON and plain text, "
                f"ensure it's a valid JSON array.\nError: {exc}"
            ) from exc

    for line in raw.split("\n"):
        for item in line.split(","):
            item = item.strip().strip("[],'\"")
            if item:
                proxies.append(_proxy_from_string(item))

    return proxies
