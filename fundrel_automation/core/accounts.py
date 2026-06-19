import json
import random
import re

from .paths import ACCOUNTS_PATH, LEGACY_ACCOUNTS_PATH

REQUIRED_ACCOUNT_FIELDS = [
    "email",
    "password",
    "firstName",
    "lastName",
    "month",
    "day",
    "year",
    "address",
    "city",
    "province",
    "postcode",
]


def load_accounts(path=ACCOUNTS_PATH):
    if path == ACCOUNTS_PATH and not path.exists() and LEGACY_ACCOUNTS_PATH.exists():
        path = LEGACY_ACCOUNTS_PATH

    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as f:
        accounts = json.load(f)

    if isinstance(accounts, dict):
        return [accounts]
    if isinstance(accounts, list):
        return accounts

    raise ValueError("Accounts file must contain a JSON object or list.")


def save_accounts(accounts, path=ACCOUNTS_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(accounts, f, indent=4)


def clean_special_characters(text):
    cleaned = re.sub(r"[^a-zA-Z0-9]", "", text or "")
    return cleaned.lower()


def validate_account(config):
    for field in REQUIRED_ACCOUNT_FIELDS:
        if not config.get(field):
            return False, f"Missing required field: {field}"

    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", config["email"]):
        return False, f"Invalid email format: {config['email']}"

    return True, "valid"


def prepare_account_config(account_data, default_config):
    current_config = default_config.copy()
    current_config.update(account_data)

    first_name = clean_special_characters(current_config.get("firstName", "first"))
    last_name = clean_special_characters(current_config.get("lastName", "last"))
    current_config["username"] = f"{last_name}{first_name}{random.randint(1000, 9999)}"

    if len(current_config.get("password", "")) < 8:
        new_password = f"{current_config.get('password', '')}{last_name}"
        current_config["password"] = new_password
        account_data["password"] = new_password

    return current_config
