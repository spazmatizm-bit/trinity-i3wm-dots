#!/bin/bash
set -e

REPO_URL="https://github.com/spazmatizm-bit/trinity-i3wm-dots.git"
TMP_DIR=$(mktemp -d)

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Trinity i3wm — Bootstrap"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

command -v pacman >/dev/null || { echo "✗ Arch Linux required"; exit 1; }
[ "$EUID" -eq 0 ] && { echo "✗ Не от root"; exit 1; }

echo "==> Installing prerequisites..."
for pkg in git wget tar curl; do
    command -v $pkg >/dev/null || sudo pacman -S --needed --noconfirm $pkg
done

echo ""
echo "==> Cloning Trinity..."
cd "$TMP_DIR"
git clone "$REPO_URL" trinity

cd trinity
chmod +x install.sh

echo ""
echo "==> Running installer..."
./install.sh

cd ~
rm -rf "$TMP_DIR"
