#!/bin/bash

set -e

setup_mocks() {
    find mocks/* -type dir \
        | sed -nE 's|mocks/(.+)|\1|p' \
        > mocks/FOLDERS.txt

    while IFS= read -r folder || [[ -n $folder ]]; do
        cp -r "mocks/$folder" .
    done < <(cat mocks/FOLDERS.txt)
}

cleanup_mocks() {
    while IFS= read -r folder || [[ -n $folder ]]; do
        rm -rf "$folder"
    done < <(cat mocks/FOLDERS.txt)
}

# Register the cleanup function to run on EXIT
# (and optionally signals like SIGINT)
trap cleanup_mocks EXIT

python3 -m coverage --help 2>&1 > /dev/null \
    || python3 -m pip install coverage

setup_mocks

python3 -m coverage run -m unittest tests/**
python3 -m coverage report
python3 -m coverage xml
