#!/bin/bash
cpu=$(top -bn1 | awk '/Cpu\(s\)/ {printf "%d", $2}')
mem=$(free | awk '/Mem:/ {printf "%d", $3/$2*100}')
printf "  %s%%   %s%%\n" "$cpu" "$mem"
