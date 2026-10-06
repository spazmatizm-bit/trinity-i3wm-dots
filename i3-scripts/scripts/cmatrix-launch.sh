#!/bin/bash
pkill -x cmatrix 2>/dev/null
sleep 0.2
exec kitty --class cmatrix -e cmatrix -C cyan -b
