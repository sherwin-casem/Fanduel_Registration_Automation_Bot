from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
ASSETS_DIR = BASE_DIR / "assets"
IMAGE_TARGETS_DIR = ASSETS_DIR / "image_targets"
DATA_DIR = BASE_DIR / "data"
ACCOUNTS_PATH = DATA_DIR / "accounts.json"
SETTINGS_PATH = DATA_DIR / "settings.json"
LEGACY_ACCOUNTS_PATH = BASE_DIR / "accounts.json"
LEGACY_SETTINGS_PATH = BASE_DIR / "settings.json"
ENV_PATH = BASE_DIR / ".env"
RUNTIME_DIR = BASE_DIR / "runtime"
RESULTS_DIR = BASE_DIR / "images_result"


def asset_path(filename):
    image_target = IMAGE_TARGETS_DIR / filename
    if image_target.exists():
        return image_target
    return BASE_DIR / filename


def workspace_path(path):
    path = Path(path)
    if path.is_absolute():
        return path
    return BASE_DIR / path
