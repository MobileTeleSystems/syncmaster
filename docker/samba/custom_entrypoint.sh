#!/usr/bin/env bash

# allow create files and directories
mkdir -p /share/folder
chmod 0777 /share/folder
/entrypoint.sh -u "1000:1000:syncmaster:syncmaster:test_only" -s "SmbShare:/share/folder:rw:syncmaster"
