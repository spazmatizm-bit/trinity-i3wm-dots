#!/bin/bash
if pgrep -f "localmusapp/main.py" >/dev/null; then
    pkill -f "localmusapp/main.py"
else
    setsid python3 "$HOME/Documents/localmusapp/main.py" >/dev/null 2>&1 &
fi
