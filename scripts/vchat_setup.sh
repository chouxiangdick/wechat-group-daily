#!/usr/bin/env bash
# vchat_setup.sh — one-shot installer for vchat CLI.
# Tested on macOS 14 (Apple Silicon), Ubuntu 22.04, and Windows 10/11
# (run inside Git Bash or WSL).
#
# Usage:  bash scripts/vchat_setup.sh
#
# After this, run `vchat setup` once interactively to import your local
# WeChat keys, then `vchat doctor` to confirm all local dbs are decrypted.

set -euo pipefail

VCHAT_REPO="${VCHAT_REPO:-https://github.com/xiangruiai/vantasma-toolkit}"
VCHAT_DIR="${VCHAT_DIR:-$HOME/vantasma-toolkit}"

echo "==> Cloning $VCHAT_REPO"
if [ -d "$VCHAT_DIR" ]; then
  echo "    already exists at $VCHAT_DIR, pulling latest"
  git -C "$VCHAT_DIR" pull --rebase --autostash
else
  git clone "$VCHAT_REPO" "$VCHAT_DIR"
fi

cd "$VCHAT_DIR/cli/vchat"

echo "==> Running install.sh"
if [ -f install.sh ]; then
  bash install.sh
else
  echo "    no install.sh found, skipping (CLI may already be on PATH)"
fi

echo "==> Installing Python deps"
pip install --upgrade pip
pip install cryptography zstandard lunardate playwright

echo "==> Installing Playwright browsers (for HTML→PNG)"
python -m playwright install chromium

echo "==> vchat version"
vchat --version || true

echo ""
echo "Next steps:"
echo "  1) Make sure the WeChat desktop client is RUNNING and LOGGED IN"
echo "  2) Run:  vchat setup     (interactive — imports your local keys)"
echo "  3) Run:  vchat doctor    (should report all local dbs decrypted)"
echo ""
echo "If vchat doctor says it cannot find your WeChat install, set the"
echo "WECHAT_INSTALL_DIR env var to your actual WeChat Files path."
