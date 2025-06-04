#!/usr/bin/python3
import os, sys
import aui
import text
import gi
from helpers import log

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk


class CopyFileContentAction:
    def __init__(self, file_path: str) -> None:
        self._file_path = file_path
        self._win_icon = aui.get_action_icon_path(text.UUID)

    def check_file_read_perms(self) -> None:
        if not os.access(self._file_path, os.R_OK):
            dialog = aui.InfoDialogWindow(
                window_icon_path=self._win_icon,
                title=text.ACTION_TITLE,
                message=text.UNREADABLE_FILE,
            )
            dialog.run()
            dialog.destroy()
            log("File is not readable.")
            exit(1)
    
    def copy_to_clipboard(self) -> None:
        try:
            with open(self._file_path, "r") as file:
                content = file.read()
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(content, -1)
            clipboard.store()
            # TODO: consider showing a dialog to confirm the action success,
            #       which could also be disable with a dont show again button.
            log("Content copied to clipboard.")
        except Exception as e:
            dialog = aui.InfoDialogWindow(
                window_icon_path=self._win_icon,
                title=text.ACTION_TITLE,
                message=text.COPY_FAILED,
            )
            dialog.run()
            dialog.destroy()
            log("Exception:", e)
            exit(1)

    def run(self) -> None:
        self.check_file_read_perms()
        self.copy_to_clipboard()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        log("Usage: ./action.py <file_path>")
        exit(1)

    file_path = sys.argv[1].replace("\\ ", " ")
    action = CopyFileContentAction(file_path=file_path)
    action.run()
