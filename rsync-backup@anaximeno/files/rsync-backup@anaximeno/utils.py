import os
import json
import text


NEMO_DEBUG = os.environ.get("NEMO_DEBUG", "")
DEBUG = "Actions" in NEMO_DEBUG if NEMO_DEBUG else False


def log(*args, **kwargs):
    """Log debug messages if DEBUG is enabled."""
    if DEBUG is True:
        print(f"Action {text.UUID}:", *args, **kwargs)


def get_tmp_store_path() -> str:
    def make_tmp_dir(path: str) -> str:
        tmp_dir = os.path.join(path, text.UUID)
        os.makedirs(tmp_dir, exist_ok=True)
        return tmp_dir

    """Get a temporary storage path."""
    if os.environ.get("XDG_RUNTIME_DIR"):
        return make_tmp_dir(os.environ["XDG_RUNTIME_DIR"])
    elif os.path.exists("~/.cache"):
        return make_tmp_dir(os.path.join(os.path.expanduser("~/.cache"), text.UUID))
    elif os.path.exists("/tmp"):
        return make_tmp_dir("/tmp")
    elif os.path.exists("/var/tmp"):
        return make_tmp_dir("/var/tmp")
    else:
        os.makedirs(os.path.expanduser("~/.cache"), exist_ok=True)
        if os.path.exists("~/.cache"):
            return make_tmp_dir(os.path.expanduser("~/.cache"))
        else:
            log("Warn: Couldn't find a temporary storage path, using the current directory")
            return os.getcwd()


def _get_config_file_path() -> str:
    config_home = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
        os.path.expanduser("~"), ".config"
    )
    config_dir = os.path.join(config_home, text.UUID)
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "config.json")


def get_last_destination() -> str:
    """Returns the last folder chosen as a backup destination, or an empty string."""
    config_file = _get_config_file_path()
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                return json.load(f).get("last_destination", "")
        except Exception as e:
            log("Warning: Couldn't read config file:", e)
    return ""


def set_last_destination(path: str) -> None:
    """Stores the given folder as the last folder chosen as a backup destination."""
    config_file = _get_config_file_path()
    try:
        with open(config_file, "w") as f:
            json.dump({"last_destination": path}, f)
    except Exception as e:
        log("Warning: Couldn't write config file:", e)
