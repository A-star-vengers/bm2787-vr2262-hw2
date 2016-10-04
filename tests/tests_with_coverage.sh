#!/usr/bin/env bash
set -e
echo "Installing coverage if necessary..."
pip install coverage --upgrade > /dev/null
coverage erase
coverage run --source=demo,demonstration.py --branch -m unittest ${@-discover tests}
coverage html
coverage report -m
