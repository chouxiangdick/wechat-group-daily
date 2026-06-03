#!/usr/bin/env python3
"""群日报·手机版 v3.0 主编排脚本。

吃 story.json + plan-mobile.json + avatars.json，依次跑：
  1. render_mobile.py  → HTML
  2. html_to_png_mobile.py → PNG 长图（900px 宽）

用法：
  python3 make_daily.py \\
      --story /tmp/story_<YYYY-MM-DD>_<群名>.json \\
      --plan /tmp/layout-plan-<YYYY-MM-DD>-<群名>-mobile.json \\
      --out-dir ~/Desktop/<群名>日报

输出：
  <out-dir>/群日报_<群名>_<日期>_手机版.html
  <out-dir>/群日报_<群名>_<日期>_手机版.png
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def run(cmd, **kwargs):
    print(f"$ {' '.join(cmd)}", file=sys.stderr)
    subprocess.run(cmd, check=True, **kwargs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--story", required=True, help="story.json 路径")
    ap.add_argument("--plan", required=True, help="layout-plan-mobile.json 路径")
    ap.add_argument("--avatars", default="",
                    help="avatars.json 路径（可选，可由 group-daily 复用）")
    ap.add_argument("--out-dir", default="",
                    help="输出目录（默认 ~/Desktop/<群名>日报/）")
    ap.add_argument("--name-suffix", default="",
                    help="文件名后缀，例如 _draft")
    ap.add_argument("--no-open", action="store_true",
                    help="生成后不自动打开")
    ap.add_argument("--no-png", action="store_true",
                    help="只生成 HTML，不截 PNG")
    args = ap.parse_args()

    story_path = os.path.expanduser(args.story)
    plan_path = os.path.expanduser(args.plan)

    with open(story_path, encoding="utf-8") as f:
        story = json.load(f)
    with open(plan_path, encoding="utf-8") as f:
        plan = json.load(f)

    # 自动找 avatars.json（如果没传）
    avatars_path = args.avatars
    if not avatars_path:
        # 默认从 plan/avatars 约定路径找
        candidate = str(Path(plan_path).parent / "avatars.json")
        if os.path.exists(candidate):
            avatars_path = candidate
        else:
            # 退回到 /tmp/avatars.json
            candidate = "/tmp/avatars.json"
            if os.path.exists(candidate):
                avatars_path = candidate
            else:
                sys.exit("找不到 avatars.json，请用 --avatars 指定")
    avatars_path = os.path.expanduser(avatars_path)

    # 输出目录
    group = story.get("group_name", "群")
    date = story.get("date", "未知日期")
    if args.out_dir:
        out_dir = Path(os.path.expanduser(args.out_dir))
    else:
        # 默认: ~/Desktop/<群名>日报
        out_dir = Path.home() / "Desktop" / f"{group}日报"
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = f"群日报_{group}_{date}{args.name_suffix}_手机版"
    html_path = out_dir / f"{stem}.html"
    png_path = out_dir / f"{stem}.png"

    # 1. 渲染 HTML
    run([
        sys.executable, str(SCRIPT_DIR / "render_mobile.py"),
        story_path, avatars_path, plan_path, str(html_path),
    ])

    # 2. 截 PNG（可选）
    if not args.no_png:
        run([
            sys.executable, str(SCRIPT_DIR / "html_to_png_mobile.py"),
            "--html", str(html_path),
            "--out", str(png_path),
            "--width", "900",
            "--scale", "2",
        ])

    print(f"\n✅ 生成完成", file=sys.stderr)
    print(f"   HTML: {html_path}", file=sys.stderr)
    if not args.no_png:
        print(f"   PNG:  {png_path}", file=sys.stderr)

    # 自动打开（macOS / Windows / Linux）
    if not args.no_open:
        try:
            if sys.platform == "darwin":
                subprocess.run(["open", str(html_path)])
                if not args.no_png:
                    subprocess.run(["open", str(png_path)])
            elif sys.platform.startswith("win"):
                os.startfile(str(html_path))
                if not args.no_png:
                    os.startfile(str(png_path))
            else:
                subprocess.run(["xdg-open", str(html_path)])
        except Exception as e:
            print(f"⚠️  自动打开失败: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
