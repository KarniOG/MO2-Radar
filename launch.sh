#!/bin/bash
if [ "$(id -u)" != "0" ]; then
	echo "Run this script as root!"
	exit 1
fi

if [ ! -d ".venv" ]; then
	echo "Run \"sh setup.sh\" first!"
	exit 1
fi

. .venv/bin/activate
.venv/bin/python3 -OO main.py
