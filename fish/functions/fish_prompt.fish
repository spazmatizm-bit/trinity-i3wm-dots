function fish_prompt
    set -l last_status $status

    set -l theme_file "$HOME/.config/theme-current.json"
    set -l c_accent "#88c0d0"
    set -l c_secondary "#9c9c9c"
    set -l c_green "#a3be8c"
    set -l c_red "#bf616a"
    set -l c_yellow "#ebcb8b"

    if test -f $theme_file
        set c_accent (python3 -c "import json; print(json.load(open('$theme_file')).get('blue', '#88c0d0'))" 2>/dev/null; or echo "#88c0d0")
        set c_secondary (python3 -c "import json; print(json.load(open('$theme_file')).get('fg_alt', '#9c9c9c'))" 2>/dev/null; or echo "#9c9c9c")
        set c_green (python3 -c "import json; print(json.load(open('$theme_file')).get('green', '#a3be8c'))" 2>/dev/null; or echo "#a3be8c")
        set c_red (python3 -c "import json; print(json.load(open('$theme_file')).get('red', '#bf616a'))" 2>/dev/null; or echo "#bf616a")
        set c_yellow (python3 -c "import json; print(json.load(open('$theme_file')).get('yellow', '#ebcb8b'))" 2>/dev/null; or echo "#ebcb8b")
    end

    set_color $c_accent
    echo -n (whoami)
    set_color normal
    echo -n "@"
    set_color $c_secondary
    echo -n (string split . $hostname)[1]
    set_color normal

    echo -n " "
    set_color $c_green
    echo -n (prompt_pwd)
    set_color normal

    if set -q git_branch
        set_color $c_yellow
        echo -n " ("(git branch --show-current)")"
        set_color normal
    end

    if test $last_status -eq 0
        set_color $c_accent
        echo -n ">"
    else
        set_color $c_red
        echo -n ">"
    end
    set_color normal
    echo -n " "
end
