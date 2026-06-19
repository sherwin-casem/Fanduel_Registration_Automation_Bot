from .paths import ENV_PATH


def load_env(path=ENV_PATH):
    values = {}
    if not path.exists():
        return values

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'\"")
            if key:
                values[key] = value

    return values


def split_env_list(value):
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]
