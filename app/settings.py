import asyncio
import copy
import os

import yaml

SETTINGS_PATH = os.path.join(os.environ.get("DATA_DIR", "/data"), "settings.yaml")

DEFAULT_SETTINGS = {
    "prowlarr": {
        "url": "",
        "api_key": "",
        "tags": [],
    },
    "qbittorrent": {
        "url": "",
        "username": "",
        "password": "",
        "download_dir": "",
    },
    "sabnzbd": {
        "url": "",
        "api_key": "",
    },
    "audiobookshelf": {
        "url": "",
        "api_key": "",
        "library_id": [],
    },
    "hardcover": {
        "api_key": "",
        "preferred_language": "English",
    },
    "notifications": {
        "urls": "",
        "batch_window": 60,
    },
    "general": {
        "group_series_in_search": True,
        "output_dir": "/output",
        "separate_type_dirs": True,
        "audiobook_prefix": "",
        "ebook_prefix": "",
        "merge_multifile_audiobooks": False,
        "public_url": "",
        "allowed_audiobook_formats": ["m4b", "mp3", "flac"],
        "allowed_ebook_formats": ["epub", "pdf", "mobi", "azw3"],
    },
    "schedule": {
        "library_sync": "0 2 * * *",
        "cache_refresh": "0 3 * * *",
        "auto_search": "0 */6 * * *",
    },
    "auth": {
        "form_enabled": False,
        "oidc_enabled": False,
        "session_secret": "",
        "session_days": 30,
        "oidc_provider_url": "",
        "oidc_client_id": "",
        "oidc_client_secret": "",
        "oidc_scopes": "openid email profile",
    },
}

_settings_lock = asyncio.Lock()


def _deep_merge(base: dict, override: dict) -> dict:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


async def get_settings() -> dict:
    async with _settings_lock:
        try:
            with open(SETTINGS_PATH) as f:
                on_disk = yaml.safe_load(f) or {}
        except FileNotFoundError:
            on_disk = {}
        return _deep_merge(DEFAULT_SETTINGS, on_disk)


async def save_settings(partial: dict) -> None:
    async with _settings_lock:
        try:
            with open(SETTINGS_PATH) as f:
                current = yaml.safe_load(f) or {}
        except FileNotFoundError:
            current = {}

        merged = _deep_merge(current, partial)
        tmp_path = SETTINGS_PATH + ".tmp"
        with open(tmp_path, "w") as f:
            yaml.dump(merged, f, default_flow_style=False, allow_unicode=True)
        os.replace(tmp_path, SETTINGS_PATH)
