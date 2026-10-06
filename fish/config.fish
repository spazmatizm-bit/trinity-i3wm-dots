# ~/.config/fish/config.fish

if status is-interactive
    zoxide init fish | source
    fzf --fish | source
end

alias please='doas'

# ===== Trixity greeting =====
function fish_greeting
    fastfetch
    echo ""
    echo "Welcome back, $USER."
    echo ""
end
