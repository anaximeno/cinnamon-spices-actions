import os
import gettext

UUID = "copy-file-content@anaximeno"
HOME = os.path.expanduser("~")
gettext.bindtextdomain(UUID, os.path.join(HOME, ".local/share/locale"))
gettext.textdomain(UUID)


_ = lambda message: gettext.gettext(message)


ACTION_TITLE = _("Copy file content")

UNREADABLE_FILE = _("Cannot read file, make sure you have proper read permissions. Operation cancelled.")

COPY_SUCCESS = _("Content copied to clipboard.")

COPY_FAILED = _("Failed to copy content to clipboard.")

DONT_SHOW_AGAIN = _("Don't show again")
