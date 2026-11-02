#!/usr/bin/python3
import os
import re
import sys
import subprocess

import aui
import text
import gi

gi.require_version("GLib", "2.0")
from gi.repository import GLib
from pathlib import Path
from utils import log, get_tmp_store_path, get_last_destination, set_last_destination


PROGRESS_PERCENT_REGEX = r"(\d{1,3})%"

# rsync exit codes for a run that finished but skipped some files
# (e.g. unsupported characters on the destination filesystem, or a
# source file that vanished mid-transfer), rather than failing outright.
RSYNC_PARTIAL_TRANSFER_CODES = (23, 24)

RSYNC_ERROR_LINE_REGEX = re.compile(r"^rsync(?:\d)?:|^rsync error:")


def escape(value) -> str:
    return GLib.markup_escape_text(str(value))


def terminal_lines(content: str) -> list[str]:
    """Collapses \\r-driven progress updates the way a terminal would, returning
    the final visible text of each newline-terminated (or still in-flight) line.
    """
    lines = []
    for block in content.split("\n"):
        visible = block.split("\r")[-1].strip()
        if visible:
            lines.append(visible)
    return lines


class RsyncBackupAction:
    def __init__(self, source: str) -> None:
        self._source = Path(source).resolve()
        self._win_icon_path = aui.get_action_icon_path(text.UUID)
        self._rsync_process = None
        self._rsync_process_log_file_path = None
        self._cancelled = False

    @property
    def rsync_process_log_file_path(self):
        if self._rsync_process_log_file_path is None:
            tmp_store_path = get_tmp_store_path()
            self._rsync_process_log_file_path = os.path.join(
                tmp_store_path, f"rsync-backup@nemo-action:backup-{os.getpid()}.txt"
            )
        return self._rsync_process_log_file_path

    def _get_start_folder(self) -> str:
        last_destination = get_last_destination()
        if last_destination and os.path.isdir(last_destination):
            return last_destination

        user = os.environ.get("USER", "")
        for candidate in (f"/run/media/{user}", f"/media/{user}", "/mnt", str(Path.home())):
            if candidate and os.path.isdir(candidate):
                return candidate

        return str(Path.home())

    def prompt_user_for_destination(self) -> str | None:
        window = aui.FolderChooserDialogWindow(
            title=text.CHOOSE_DESTINATION_TITLE,
            window_icon_path=self._win_icon_path,
            start_folder=self._get_start_folder(),
            select_button_text=text.OK,
        )
        response = window.run()
        window.destroy()
        return response

    def prompt_message(self, message: str, expander_label: str = "", expanded_text: str = "") -> None:
        window = aui.InfoDialogWindow(
            title=text.ACTION_TITLE,
            message=message,
            window_icon_path=self._win_icon_path,
            expander_label=expander_label,
            expanded_text=expanded_text,
        )
        window.run()
        window.destroy()

    def prompt_confirm_backup(self, destination: Path) -> bool:
        window = aui.QuestionDialogWindow(
            title=text.ACTION_TITLE,
            message=text.CONFIRM_BACKUP
            % {
                "source": f"<b>{escape(self._source)}</b>",
                "destination": f"<b>{escape(destination)}</b>",
            },
            window_icon_path=self._win_icon_path,
        )
        response = window.run()
        window.destroy()
        return response == window.RESPONSE_YES

    def run_rsync_backup(self, source: Path, destination: Path) -> int:
        log(f"Info: backing up {str(source)!r}")
        log(f"Info: backup destination {str(destination)!r}")

        os.makedirs(destination, exist_ok=True)

        with open(self.rsync_process_log_file_path, "w") as rsync_log_file:
            self._rsync_process = subprocess.Popen(
                [
                    "rsync",
                    "-a",
                    "-h",
                    "--info=progress2",
                    f"{source}{os.sep}",
                    f"{destination}{os.sep}",
                ],
                stdout=rsync_log_file,
                stderr=subprocess.STDOUT,
            )

            window = aui.ProgressbarDialogWindow(
                title=text.ACTION_TITLE,
                message=text.BACKING_UP % source,
                window_icon_path=self._win_icon_path,
                timeout_callback=self._handle_progress,
                on_cancel_callback=self._handle_cancel,
                timeout_ms=55,
            )

            window.run()
            window.destroy()

        return self._rsync_process.poll()

    def run(self) -> None:
        if not self._source.is_dir():
            exit(1)

        destination_dir = self.prompt_user_for_destination()

        if not destination_dir:
            log("Info: User cancelled the operation")
            exit(0)

        destination = Path(destination_dir).resolve().joinpath(self._source.name)

        if destination == self._source:
            self.prompt_message(text.SAME_AS_SOURCE)
            exit(1)

        if str(destination).startswith(f"{self._source}{os.sep}"):
            self.prompt_message(text.DESTINATION_INSIDE_SOURCE)
            exit(1)

        if not self.prompt_confirm_backup(destination):
            log("Info: User cancelled the operation")
            exit(0)

        returncode = self.run_rsync_backup(self._source, destination)

        if self._cancelled:
            self.prompt_message(text.BACKUP_CANCELLED)
            self._cleanup()
            exit(0)
        elif returncode == 0:
            set_last_destination(str(destination.parent))
            self.prompt_successful_backup(destination)
            self._cleanup()
            exit(0)
        elif returncode in RSYNC_PARTIAL_TRANSFER_CODES:
            set_last_destination(str(destination.parent))
            self.prompt_partial_backup(destination)
            self._cleanup()
            exit(0)
        else:
            self.prompt_unsuccessful_backup(destination)
            exit(1)

    def _read_log_lines(self) -> list[str]:
        if not os.path.exists(self.rsync_process_log_file_path):
            return []
        with open(self.rsync_process_log_file_path, "r", errors="ignore") as rsync_log_file:
            return terminal_lines(rsync_log_file.read())

    def _get_last_progress_line(self) -> str | None:
        lines = self._read_log_lines()
        return lines[-1] if lines else None

    def _handle_progress(self, user_data, window: aui.ProgressbarDialogWindow) -> bool:
        if self._rsync_process and self._rsync_process.poll() is None:
            last_line = self._get_last_progress_line()
            if last_line is not None:
                match = re.search(PROGRESS_PERCENT_REGEX, last_line)
                if match:
                    window.progressbar.set_fraction(min(int(match.group(1)) / 100, 1.0))
                else:
                    window.progressbar.pulse()
                window.progressbar.set_text(last_line)
            else:
                window.progressbar.pulse()

        if self._rsync_process and self._rsync_process.poll() is not None:
            window.stop()
            window.destroy()
            return False

        return True

    def _handle_cancel(self) -> None:
        self._rsync_process.kill()
        self._cancelled = True

    def _cleanup(self) -> None:
        if os.path.exists(self.rsync_process_log_file_path):
            try:
                os.remove(self.rsync_process_log_file_path)
                log("Info: Removed rsync process log file:", self.rsync_process_log_file_path)
            except Exception as e:
                log("Warning: Couldn't remove rsync process log file:", e)

    def prompt_successful_backup(self, destination: Path):
        log(f"Info: {str(self._source)!r} was successfully backed up")
        open_destination_button = aui.ActionableButton(
            text.OPEN_DESTINATION_FOLDER, lambda: self.on_opening_destination_folder(destination)
        )
        ok_button = aui.ActionableButton(text.OK, lambda: None)
        window = aui.ActionableDialogWindow(
            title=text.ACTION_TITLE,
            message=text.SUCCESSFUL_BACKUP,
            window_icon_path=self._win_icon_path,
            buttons=[open_destination_button, ok_button],
            active_button_text=text.OK,
        )
        window.run()
        window.destroy()

    def prompt_partial_backup(self, destination: Path):
        log(f"Warning: backup to {str(destination)!r} finished with errors")

        error_lines = [
            line for line in self._read_log_lines() if RSYNC_ERROR_LINE_REGEX.match(line)
        ]
        log("Warning: rsync errors:", error_lines)

        open_destination_button = aui.ActionableButton(
            text.OPEN_DESTINATION_FOLDER, lambda: self.on_opening_destination_folder(destination)
        )
        ok_button = aui.ActionableButton(text.OK, lambda: None)
        window = aui.ActionableDialogWindow(
            title=text.ACTION_TITLE,
            message=text.PARTIAL_BACKUP,
            window_icon_path=self._win_icon_path,
            buttons=[open_destination_button, ok_button],
            active_button_text=text.OK,
            expander_label=text.BACKUP_ERRORS if error_lines else "",
            expanded_text=escape("\n".join(error_lines)),
        )
        window.run()
        window.destroy()

    def on_opening_destination_folder(self, destination: Path):
        try:
            subprocess.Popen(
                ["xdg-open", str(destination)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            log(f"Error: Couldn't open the destination folder: {e}")
            self.prompt_message(text.UNSUCCESSFUL_OPEN_DESTINATION_FOLDER)

    def prompt_unsuccessful_backup(self, destination: Path):
        log(f"Error: backup to {str(destination)!r} wasn't successful")

        full_log = "\n".join(self._read_log_lines())
        log("Error: rsync log:", full_log)

        self.prompt_message(
            text.UNSUCCESSFUL_BACKUP % f"<b>{escape(destination)}</b>",
            expander_label=text.BACKUP_INFO if full_log else "",
            expanded_text=escape(full_log),
        )


if __name__ == "__main__":
    source = sys.argv[1].replace("\\ ", " ")
    action = RsyncBackupAction(source)
    action.run()
