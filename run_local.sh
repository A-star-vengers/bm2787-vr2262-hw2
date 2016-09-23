#!/usr/bin/env sh
if [ ! -f COOKIE_SECRET ]; then
    head -c 24 /dev/urandom > COOKIE_SECRET
fi
./demonstration.py
