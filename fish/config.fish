# ~/.config/fish/config.fish

alias please='doas'

# ===== Trixity greeting =====
function fish_greeting
    fastfetch
    echo ""
    echo "Welcome back, $USER."
    echo ""
end
