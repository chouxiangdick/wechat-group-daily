---
name: wechat-group-daily
description: |
  End-to-end pipeline: pull a WeChat (微信) group's chat history from a local PC
  installation, decrypt V2 .dat image attachments, and render a magazine-style
  daily newspaper (HTML + 900px long PNG, mobile-first) — or an optional A3
  printable PDF. Use when the user says "做群日报 / 给 XX 群做日报 / 整理一下
  今天 XX 群 / 微信群日报 / WeChat group daily". A3 variant triggers on
  "做报纸版 / 印刷版 / A3".
version: 1.0.0
---

# WeChat Group Daily — Skill

End-to-end skill that takes a WeChat group + a date and produces a mobile-ready
HTML + 900px long PNG daily newspaper. Internally chains:

```
vchat setup  →  vchat history  →  V2 .dat image decrypt  →
write story + plan  →  render HTML  →  chrome headless PNG  →
verify_daily.py self-check  →  ship
```

Default output = **mobile (900px wide long PNG)**. Trigger `报纸版 / 印刷版 / A3`
to get the A3 PDF variant instead.

---

## When to trigger

- "做群日报" / "给 XX 群做日报" / "整理一下今天 XX 群" / "微信群日报"
- "做报纸版" / "印刷版" / "A3" — switches output to A3 newspaper PDF

## What you actually do

A 6-step pipeline. **Run them in order; do not skip.**

### Step 0 — Install vchat CLI (one-time)

```bash
git clone https://github.com/xiangruiai/vantasma-toolkit
cd vantasma-toolkit/cli/vchat
bash install.sh
pip install cryptography zstandard
sudo vchat setup          # macOS / Linux
vchat setup               # Windows (already elevated PowerShell)
vchat doctor              # confirm all local db decrypted
```

If `vchat doctor` reports missing dbs on Windows, see `references/data-sources.md`
— your WeChat install path is non-default. Set `WECHAT_INSTALL_DIR` env var or
edit `vchat_core/find_keys_windows.py` to add your path as a candidate.

### Step 0.5 — Verify vchat is usable

```bash
vchat groups | head -20     # list groups
vchat history "你的群名" -n 5 # pull 5 messages as a smoke test
```

**Windows encoding caveat**: PowerShell defaults to GBK. Always set
`[Console]::OutputEncoding = [System.Text.Encoding]::UTF8` before reading
chat logs, or you'll get mojibake.

### Step 1 — Pull chat history for the target date

```bash
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8   # Windows
vchat history "<群名>" -n 5000 > /tmp/chat_log_<YYYY-MM-DD>_<群名>.txt
```

5000 lines is enough for a one-day 200-active-member group.

### Step 1.5 — Decrypt V2 .dat images (optional but recommended)

V2 .dat is AES-128-ECB encrypted. The 16-byte key is held in the WeChat
process memory and must be extracted before it exits. On macOS / Linux, use
the vchat-builtin tool. On Windows:

```bash
python scripts/find_image_key_windows.py     # scans Weixin.exe memory
                                             # writes ~/.vchat/data/config.json
```

Then decrypt images:

```bash
python scripts/decrypt_images.py \
  --in  "$WECHAT_INSTALL_DIR/xwechat_files/<wxid>/db_storage/hardlink/<YYYY-MM>/<Img|Video>" \
  --out ./imgs_<date>_<群名>/
```

> **Note**: image description via `describe_images` MCP is currently
> unreliable. Don't include image captions in the rendered daily unless
> the user has explicitly described them. Quote-strict mode covers text
> only — image content is treated as opaque.

### Step 2 — Read the chat log + write `story.json`

Read `/tmp/chat_log_<date>_<群名>.txt`. Understand semantics, identify
arcs (timeline, casts, stats, lingo, Q&A), then write
`/tmp/story_<date>_<群名>.json`. Schema in `references/story-schema.md`.

**Date utilities**:

```python
from datetime import date
from lunardate import LunarDate

d = date(2026, 6, 2)
weekday_cn = ["周一","周二","周三","周四","周五","周六","周日"][d.weekday()]
lunar = LunarDate.fromSolarDate(d.year, d.month, d.day)
# → 丙午年四月十七
```

**Never hand-write 干支 lunar dates** — use `lunardate` lib (install via
`pip install lunardate`). One off-by-one digit and the whole daily is
mis-stamped.

### Step 3 — Write `plan.json` (mobile or A3)

Mobile (`examples/plan.template.json`) is a 900px-wide single-column card
flow: lead → hero timeline → cast cards → stats → quotes → lingo → footer.
A3 (`examples/plan-template-a3.json`) is 4 newspaper pages of 1587px each.

**Every quote you include MUST appear verbatim in the chat log file.**
No merging of multiple lines, no typo correction, no paraphrase. The
verifier will catch mismatches and fail the build.

### Step 4 — Render HTML + PNG

```bash
python scripts/make_daily.py \
  --story /tmp/story_<date>_<群名>.json \
  --plan  /tmp/plan_<date>_<群名>.json \
  --out   ./<群日报名>_<date>_<variant>
```

Outputs `<name>.html` (source) and `<name>.png` (900×<height>px long image).
For A3, outputs `<name>.html` + `<name>.pdf`.

### Step 5 — Self-check (mandatory)

```bash
python scripts/verify_daily.py \
  --date     2026-06-02 \
  --weekday  周二 \
  --chat-log /tmp/chat_log_2026-06-02_<群名>.txt \
  --story    /tmp/story_2026-06-02_<群名>.json
```

**All 4 checks MUST pass** (date / weekday / lunar / quote verbatim).
If any fails, **fix the daily, do not tweak the verifier to make it
pass.** Re-run until green.

### Step 6 — Ship

Output directory:

| Platform | Default output dir |
|---|---|
| macOS / Linux | `~/Desktop/<群名>_日报/` |
| Windows | `C:\Users\<user>\Desktop\<群名>_日报\` |

Files: `<name>.html`, `<name>.png` (or `.pdf` for A3), plus decrypted
images if Step 1.5 was run.

---

## Style

- Mobile = 宋体/朱砂红/卡片圆角阴影/严整排版. 锐评栏目名 (e.g. 头版锐评 /
  抗压实录 / 今日主演 / 锐评金句墙 / 圈内黑话).
- A3 = 报纸体话语 / 标题党 / 反讽 / 黑色幽默.
- Cast labels can use nicknames (群内梗); quotes must be verbatim.
- Pull semantic depth, don't just paste raw messages.

## What this skill does NOT do

- No real-name-to-wxid auto-resolution. Use the `vchat contacts` listing
  and cross-check; if the contact cache shows wrong names (it often does),
  ask the user.
- No image captioning. V2 .dat decrypt works; image understanding is
  out of scope until upstream MCP vision is stable.
- No multi-day rollups. One day at a time.
- No live group monitoring. One-shot batch run.

## Failure modes & recovery

| Symptom | Cause | Fix |
|---|---|---|
| `vchat doctor` reports 0 db decrypted | WeChat install path is non-default | Set `WECHAT_INSTALL_DIR` or patch `find_keys_windows.py` |
| Chat log is mojibake | PowerShell GBK | Set `[Console]::OutputEncoding = UTF8` before `vchat history` |
| `verify_daily.py` fails on quote | Quote not in chat log verbatim | Re-grep the source message; copy exact substring |
| `find_image_key_windows.py` returns no key | WeChat not running | Start WeChat desktop, log in, then re-run |
| Chromium headless crashes | Missing `chrome.exe` | Install Chrome or pass `--executable-path` to playwright |
