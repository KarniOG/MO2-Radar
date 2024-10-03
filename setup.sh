#!/bin/bash
if [ "$(id -u)" = "0" ]; then
	echo "Do not run this script as root!"
	exit 1
fi

python3 -m venv .venv
. .venv/bin/activate
.venv/bin/pip3 install -r requirements.txt
