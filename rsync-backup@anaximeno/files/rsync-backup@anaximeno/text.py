import os
import gettext

UUID = "rsync-backup@anaximeno"
HOME = os.path.expanduser("~")
gettext.bindtextdomain(UUID, os.path.join(HOME, ".local/share/locale"))
gettext.textdomain(UUID)


def _(message: str) -> str:
    return gettext.gettext(message)


ACTION_TITLE = _("Rsync Backup")

CHOOSE_DESTINATION_TITLE = _("Choose the backup destination")

DESTINATION_INSIDE_SOURCE = _(
    "The destination is inside the folder being backed up. Please choose a different destination."
)

SAME_AS_SOURCE = _(
    "The destination is the same as the folder being backed up. Please choose a different destination."
)

CONFIRM_BACKUP = _(
    "Backup %(source)s\ninto\n%(destination)s ?"
)

BACKING_UP = _("Backing up %s")

SUCCESSFUL_BACKUP = _("Folder successfully backed up!")

PARTIAL_BACKUP = _(
    "Backup finished, but some item(s) could not be copied, likely because the destination "
    "filesystem doesn't support some characters used in their names (e.g. FAT/exFAT drives don't "
    "allow ':' in filenames). See details below."
)

BACKUP_ERRORS = _("Errors")

OPEN_DESTINATION_FOLDER = _("Open")

OK = _("Ok")

UNSUCCESSFUL_OPEN_DESTINATION_FOLDER = _("Couldn't open the destination folder!")

UNSUCCESSFUL_BACKUP = _("Error backing up to: %s")

BACKUP_INFO = _("Backup info")

BACKUP_CANCELLED = _("The backup was cancelled. The destination folder may contain a partial copy.")
