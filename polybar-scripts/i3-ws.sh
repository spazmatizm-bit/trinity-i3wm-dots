#!/bin/bash
ws=$(i3-msg -t get_workspaces 2>/dev/null)
[ -z "$ws" ] && exit 0

echo "$ws" | tr ',' '\n' | tr -d '{}[]"' | awk -F: '
  /name:/    {name=$2; gsub(/^ +| +$/,"",name)}
  /focused:/ {foc=$2;  gsub(/^ +| +$/,"",foc)}
  /visible:/ {vis=$2;  gsub(/^ +| +$/,"",vis)}
  /urgent:/  {urg=$2;  gsub(/^ +| +$/,"",urg);
              if (urg=="true")       {fg="#2e3440"; bg="#bf616a"}
              else if (foc=="true")  {fg="#2e3440"; bg="#88c0d0"}
              else if (vis=="true")  {fg="#eceff4"; bg="#4c566a"}
              else                   {fg="#6c7086"; bg="#3b4252"}
              printf "%%{F%s}%%{B%s}  %s  %%{B-}%%{F-} ", fg, bg, name
             }'
echo
