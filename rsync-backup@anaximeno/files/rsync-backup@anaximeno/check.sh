#!/bin/bash

SOURCE_DIR=$(echo $1 | sed 's/\\ / /g')

# Some locations like trash or recent don't return a valid path.
if [[ -z "$SOURCE_DIR" ]]; then
    exit 1
fi

if [[ ! -d "$SOURCE_DIR" || ! -r "$SOURCE_DIR" ]]; then
    exit 1
fi

command -v rsync >/dev/null 2>&1 || exit 1

exit 0
