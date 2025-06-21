import os
import text
import shutil


DEBUG = os.environ.get("NEMO_DEBUG") == "Actions"


def log(*args, **kwargs):
    if DEBUG:
        print(f"Action {text.UUID}:", *args, **kwargs)


def check_command_available(command: str) -> bool:
    return shutil.which(command) is not None


def check_commands_available(commands_list: list[str]) -> bool:
    for cmd in commands_list:
        if not check_commands_available(cmd):
            return False
    return True
