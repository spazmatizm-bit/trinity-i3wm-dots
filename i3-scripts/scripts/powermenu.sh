#!/bin/bash
# Rofi power menu

LOCK="  Lock"
LOGOUT="  Logout"
REBOOT="  Reboot"
SHUTDOWN="  Shutdown"
SUSPEND="  Suspend"

CHOSEN=$(printf "%s\n%s\n%s\n%s\n%s" "$LOCK" "$LOGOUT" "$SUSPEND" "$REBOOT" "$SHUTDOWN" | rofi -dmenu -i -p "Power" -theme-str 'window {width: 20%;}')

case "$CHOSEN" in
    "$LOCK")     betterlockscreen -l dim ;;
    "$LOGOUT")   i3-msg exit ;;
    "$REBOOT")   systemctl reboot ;;
    "$SHUTDOWN") systemctl poweroff ;;
    "$SUSPEND")  systemctl suspend ;;
esac
