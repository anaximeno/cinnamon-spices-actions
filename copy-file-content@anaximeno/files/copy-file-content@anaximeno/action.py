#!/usr/bin/python3
import os, sys
import aui
import text
import gi
import subprocess
import shutil
from helpers import log, check_commands_available

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

SESSION = os.environ["XDG_SESSION_TYPE"]


class CopyFileContentAction:
    def __init__(self, file_path: str) -> None:
        self._file_path = file_path
        self._win_icon = aui.get_action_icon_path(text.UUID)

    def wayland_check_wl_clipboard_installed(self) -> None:
        if SESSION == "wayland" and not check_commands_available(
            ["wl-paste", "wl-copy"]
        ):
            # --
            log("wl-clipboard not installed for the wayland session.")
            dialog = aui.InfoDialogWindow(
                window_icon_path=self._win_icon,
                title=text.ACTION_TITLE,
                message=text.WAYLAND_INSTALL_WL_CLIPBOARD,
            )
            dialog.run()
            dialog.destroy()
            exit(1)

    def check_file_read_perms(self) -> None:
        if not os.access(self._file_path, os.R_OK):
            log("File is not readable.")
            dialog = aui.InfoDialogWindow(
                window_icon_path=self._win_icon,
                title=text.ACTION_TITLE,
                message=text.UNREADABLE_FILE,
            )
            dialog.run()
            dialog.destroy()
            exit(1)

    def _perform_copy_to_clipboard_x11(self) -> bool:
        try:
            with open(self._file_path, "r") as file:
                content = file.read()
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(content, -1)
            clipboard.store()
            return True
        except Exception as e:
            log("Exception:", e)
            return False

    def _perform_copy_to_clipboard_way(self) -> bool:
        try:
            res = subprocess.run(
                ["wl-copy", "<", self._file_path], stderr=subprocess.PIPE
            )
            if res.returncode == 0:
                return True
            log("Error:", res.stderr)
            return False
        except Exception as e:
            log("Exception:", e)
            return False

    def copy_to_clipboard(self) -> None:
        success: bool = False

        if SESSION == "wayland":
            success = self._perform_copy_to_clipboard_way()
        else:  # X11
            success = self._perform_copy_to_clipboard_x11()

        if success:
            log("Content copied to clipboard.")
            dialog = aui.InfoDialogWindow(
                window_icon_path=self._win_icon,
                title=text.ACTION_TITLE,
                message=text.COPY_SUCCESS,
            )
            dialog.run()
            dialog.destroy()
        else:
            log("Content wasn't copied to clipboard.")
            dialog = aui.InfoDialogWindow(
                window_icon_path=self._win_icon,
                title=text.ACTION_TITLE,
                message=text.COPY_FAILED,
            )
            dialog.run()
            dialog.destroy()
            exit(1)

    def run(self) -> None:
        self.wayland_check_wl_clipboard_installed()
        self.check_file_read_perms()
        self.copy_to_clipboard()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        log("Usage: ./action.py <file_path>")
        exit(1)

    file_path = sys.argv[1].replace("\\ ", " ")
    action = CopyFileContentAction(file_path=file_path)
    action.run()
