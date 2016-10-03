#!/usr/bin/env sh
if [ ! -d venv ]; then
    echo "Creating virtual environment venv"
    python3 -m venv venv
fi
echo "Entering virtual environment venv"
source ./venv/bin/activate
echo "Installing requirements if necessary..."
pip install pip --upgrade > /dev/null
pip install -r requirements.txt --upgrade > /dev/null
if [ ! -f COOKIE_SECRET ]; then
    echo "Creating COOKIE_SECRET file"
    head -c 24 /dev/urandom > COOKIE_SECRET
fi
./demonstration.py
