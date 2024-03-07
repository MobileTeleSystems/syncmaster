#!/usr/bin/env bash

root_path=$(dirname $(realpath $0))
coverage combine --rcfile=syncmaster/tests/.coveragerc
coverage xml --rcfile=syncmaster/tests/.coveragerc -o $root_path/reports/coverage.xml -i
