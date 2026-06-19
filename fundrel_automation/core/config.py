import json
import re
from copy import deepcopy

from .env import load_env, split_env_list
from .paths import LEGACY_SETTINGS_PATH, SETTINGS_PATH


DEFAULT_SETTINGS = {
    "edge_path": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "referrals": [
        {
            "url": "https://fndl.co/ohhanft",
            "enabled": True,
            "percentage": 100,
        }
    ],
    "referral_mode": "rotate",
    "referral_state": {
        "index": 0,
        "start_time": 0,
        "random_bag": [],
    },
    "proxies": [],
}


def _migrate_settings(settings):
    changed = False

    if "urls" in settings and "referrals" not in settings:
        settings["referrals"] = [
            {"url": url, "enabled": True, "percentage": 100}
            for url in settings["urls"]
        ]
        settings["referral_mode"] = "rotate"
        settings["referral_state"] = {"index": 0, "start_time": 0, "random_bag": []}
        changed = True

    settings.setdefault("referrals", [])
    settings.setdefault("proxies", [])
    settings.setdefault("referral_mode", "rotate")
    settings.setdefault("referral_state", {"index": 0, "start_time": 0, "random_bag": []})
    settings.setdefault("edge_path", DEFAULT_SETTINGS["edge_path"])

    return settings, changed


def settings_from_env(env=None):
    env = env if env is not None else load_env()
    settings = deepcopy(DEFAULT_SETTINGS)

    edge_path = env.get("FUNDREL_EDGE_PATH")
    if edge_path:
        settings["edge_path"] = edge_path

    referral_mode = env.get("FUNDREL_REFERRAL_MODE")
    if referral_mode:
        settings["referral_mode"] = referral_mode

    referrals = split_env_list(env.get("FUNDREL_REFERRALS", ""))
    if referrals:
        settings["referrals"] = [
            {"url": url, "enabled": True, "percentage": 100}
            for url in referrals
        ]

    proxies = split_env_list(env.get("FUNDREL_PROXIES", ""))
    if proxies:
        settings["proxies"] = [_proxy_from_string(proxy) for proxy in proxies]

    return settings


def apply_env_defaults(settings, env=None):
    env_settings = settings_from_env(env)

    if settings.get("edge_path") == DEFAULT_SETTINGS["edge_path"]:
        settings["edge_path"] = env_settings["edge_path"]
    if not settings.get("referrals"):
        settings["referrals"] = env_settings["referrals"]
    if not settings.get("proxies"):
        settings["proxies"] = env_settings["proxies"]
    if settings.get("referral_mode") == DEFAULT_SETTINGS["referral_mode"]:
        settings["referral_mode"] = env_settings["referral_mode"]

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


def parse_referrals(raw):
    raw = raw.strip()
    referrals = []
    if not raw:
        return referrals

    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, list):
            raise ValueError("Referrals JSON must be a list.")

        for item in parsed:
            if isinstance(item, dict):
                referrals.append(item)
            elif isinstance(item, str):
                referrals.append({"url": item, "enabled": True, "percentage": 100})
        return referrals
    except Exception as exc:
        if "{" in raw:
            raise ValueError(
                "Referrals format is invalid. If mixing JSON and plain text, "
                f"ensure it's a valid JSON array.\nError: {exc}"
            ) from exc

    clean_ref = raw.strip("[]")
    for item in re.split(r"[\n,]+", clean_ref):
        item = item.strip().strip("'\"")
        if item:
            referrals.append({"url": item, "enabled": True, "percentage": 100})

    return referrals


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
