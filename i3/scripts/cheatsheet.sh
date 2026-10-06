#!/bin/bash

CONF="$HOME/.config/i3/config"

{
    printf '\n'
    printf '  \033[1;34m╭──────────────────────────────────────────────────────╮\033[0m\n'
    printf '  \033[1;34m│\033[0m  \033[1;37mi3 Keybindings\033[0m                       \033[2mq to quit · / to search\033[0m\n'
    printf '  \033[1;34m╰──────────────────────────────────────────────────────╯\033[0m\n'
    printf '\n'

    # Section: apps & launch
    printf '  \033[1;36m▸ Apps\033[0m\n'
    grep -E '^bindsym.*(exec|kitty|rofi|dmenu)' "$CONF" \
        | sed -E 's/^bindsym[[:space:]]+//' \
        | awk '{ k=$1; $1=""; sub(/^ /,""); printf "    \033[33m%-22s\033[0m %s\n", k, $0 }'
    printf '\n'

    # Section: focus & move
    printf '  \033[1;36m▸ Focus & Move\033[0m\n'
    grep -E '^bindsym.*(focus|move)' "$CONF" \
        | sed -E 's/^bindsym[[:space:]]+//' \
        | awk '{ k=$1; $1=""; sub(/^ /,""); printf "    \033[33m%-22s\033[0m %s\n", k, $0 }'
    printf '\n'

    # Section: layout
    printf '  \033[1;36m▸ Layout\033[0m\n'
    grep -E '^bindsym.*(layout|split|floating|focus mode)' "$CONF" \
        | sed -E 's/^bindsym[[:space:]]+//' \
        | awk '{ k=$1; $1=""; sub(/^ /,""); printf "    \033[33m%-22s\033[0m %s\n", k, $0 }'
    printf '\n'

    # Section: workspaces
    printf '  \033[1;36m▸ Workspaces\033[0m\n'
    grep -E '^bindsym.*workspace' "$CONF" \
        | sed -E 's/^bindsym[[:space:]]+//' \
        | awk '{ k=$1; $1=""; sub(/^ /,""); printf "    \033[33m%-22s\033[0m %s\n", k, $0 }'
    printf '\n'

    # Section: session
    printf '  \033[1;36m▸ Session\033[0m\n'
    grep -E '^bindsym.*(kill|restart|exit|lock|mode)' "$CONF" \
        | sed -E 's/^bindsym[[:space:]]+//' \
        | awk '{ k=$1; $1=""; sub(/^ /,""); printf "    \033[33m%-22s\033[0m %s\n", k, $0 }'
    printf '\n'

    # Section: media
    printf '  \033[1;36m▸ Media\033[0m\n'
    grep -E '^bindsym.*(pactl|XF86Audio)' "$CONF" \
        | sed -E 's/^bindsym[[:space:]]+//' \
        | awk '{ k=$1; $1=""; sub(/^ /,""); printf "    \033[33m%-22s\033[0m %s\n", k, $0 }'
    printf '\n'

    # Fallback: anything else
    printf '  \033[1;36m▸ Other\033[0m\n'
    grep -E '^bindsym' "$CONF" \
        | grep -vE '(exec|focus|move|layout|split|floating|workspace|kill|restart|exit|lock|mode|pactl|XF86Audio)' \
        | sed -E 's/^bindsym[[:space:]]+//' \
        | awk '{ k=$1; $1=""; sub(/^ /,""); printf "    \033[33m%-22s\033[0m %s\n", k, $0 }'
    printf '\n'
} | less -R -X

