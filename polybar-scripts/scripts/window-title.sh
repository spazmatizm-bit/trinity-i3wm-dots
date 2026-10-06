#!/bin/bash
# Get active window title via i3
title=$(i3-msg -t get_tree | python3 -c "
import sys, json
tree = json.load(sys.stdin)
def find_focused(node):
    if node.get('focused'):
        return node
    for child in node.get('nodes', []) + node.get('floating_nodes', []):
        result = find_focused(child)
        if result:
            return result
    return None

node = find_focused(tree)
if node:
    name = node.get('name', '')
    # Truncate long titles
    if len(name) > 60:
        name = name[:57] + '...'
    print(name)
")
echo "$title"
