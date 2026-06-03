#!/usr/bin/env python3
"""
patch_vchat_windows.py — idempotent compatibility patch for
vantasma-toolkit's `vchat_core/find_keys_windows.py`.

This script is a no-op if your vantasma-toolkit checkout already includes
both fixes. It only patches older versions that lack:

  1. WeChat 4.x renamed the main process from `WeChat.exe` to `Weixin.exe`.
     Older `find_wechat_pid()` only matches `WeChat.exe` and silently
     returns None, so vchat setup looks like it found no process.

  2. vchat assumed WeChat was installed at the default path
     (`%USERPROFILE%/Documents/WeChat Files`). If you installed WeChat
     elsewhere (e.g. `D:\\软件\\微信`), vchat can't find the db_storage
     directory and reports 0 db decrypted.

Usage:
    # If you cloned vantasma-toolkit to $HOME/vantasma-toolkit:
    python scripts/patch_vchat_windows.py

    # Or pass an explicit path:
    python scripts/patch_vchat_windows.py --path /opt/vantasma-toolkit/cli/vchat

The script:
  - Backs up the original file to `<file>.bak` (only on first apply).
  - Inserts the missing `elif name == "weixin.exe":` branch if absent.
  - Inserts the `WECHAT_INSTALL_DIR` env-var block if absent.
  - Re-running is a no-op; prints "already patched" and exits 0.

After patching, you still need to:
    1) Have WeChat desktop running and logged in.
    2) Run `vchat setup` once interactively.
    3) Run `vchat doctor` to confirm all dbs decrypted.

Tested on vantasma-toolkit commit range 2024-09 → 2026-06.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

WECHAT_BRANCH = "            elif name == \"weixin.exe\":\n                weixin_pids.append(entry.th32ProcessID)\n"
WECHAT_RETURN = (
    "        return (wechat_pids[0] if wechat_pids\n"
    "                else weixin_pids[0] if weixin_pids\n"
    "                else None)\n"
)
INSTALL_DIR_BLOCK = """    # 3+4 微信安装目录的子路径（扫 D:\\软件\\微信 这种自定义安装）
    # 注意：vchat 不会自动发现微信装在哪儿，需要 WECHAT_INSTALL_DIR 环境变量
    install_dir = os.environ.get(\"WECHAT_INSTALL_DIR\")
    if install_dir:
        base_dirs.extend([
            Path(install_dir) / \"WeChat Files\",
            Path(install_dir) / \"xwechat_files\",
        ])
"""


def _patch(src: Path) -> str:
    text = src.read_text(encoding="utf-8")
    changes: list[str] = []

    if 'name == "weixin.exe"' not in text:
        # Insert the elif branch right after the existing wechat.exe branch.
        anchor = '            if name == "wechat.exe":\n                wechat_pids.append(entry.th32ProcessID)\n'
        if anchor not in text:
            return f"FAIL: cannot find anchor for weixin.exe branch in {src}"
        text = text.replace(anchor, anchor + WECHAT_BRANCH, 1)
        changes.append("+ weixin.exe branch")

        # Replace the simplistic `return wechat_pids[0] if wechat_pids else None` line.
        old_return_variants = [
            "        return wechat_pids[0] if wechat_pids else None\n",
        ]
        replaced = False
        for old in old_return_variants:
            if old in text:
                text = text.replace(old, "        " + WECHAT_RETURN, 1)
                replaced = True
                break
        if not replaced:
            return f"FAIL: cannot find wechat_pids return line to update in {src}"
        changes.append("+ wechat/weixin return priority")

    if "WECHAT_INSTALL_DIR" not in text:
        anchor = "    base_dirs = [\n        Path.home() / \"Documents\" / \"WeChat Files\",\n        Path.home() / \"Documents\" / \"xwechat_files\",\n    ]\n"
        if anchor not in text:
            return f"FAIL: cannot find base_dirs anchor in {src}"
        text = text.replace(anchor, anchor + "\n" + INSTALL_DIR_BLOCK, 1)
        changes.append("+ WECHAT_INSTALL_DIR env var support")

    if not changes:
        return "already patched (no changes needed)"

    bak = src.with_suffix(src.suffix + ".bak")
    if not bak.exists():
        shutil.copy2(src, bak)
        changes.append(f"  backup → {bak.name}")

    src.write_text(text, encoding="utf-8")
    return "patched: " + ", ".join(changes)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument(
        "--path",
        default=str(Path.home() / "vantasma-toolkit" / "cli" / "vchat" / "vchat_core" / "find_keys_windows.py"),
        help="Path to vantasma-toolkit's find_keys_windows.py",
    )
    args = ap.parse_args()

    src = Path(args.path)
    if not src.exists():
        print(f"error: not found: {src}", file=sys.stderr)
        print("hint: pass --path /path/to/vantasma-toolkit/cli/vchat/vchat_core/find_keys_windows.py", file=sys.stderr)
        return 2

    result = _patch(src)
    print(f"{src}: {result}")
    return 0 if not result.startswith("FAIL") else 1


if __name__ == "__main__":
    sys.exit(main())
