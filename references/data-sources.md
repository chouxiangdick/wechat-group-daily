# Data sources — where the bytes come from

## 1. Chat history (text)

Source: WeChat desktop client's local SQLite databases. After vchat setup,
they're decrypted and copied to `~/.vchat/data/decrypted/` (macOS / Linux) or
`%USERPROFILE%\.vchat\data\decrypted\` (Windows).

Key db files for chat history:

| File | Purpose | Decrypted size (typical) |
|---|---|---|
| `message/message_0.db` | All chat messages (text, voice, image references, file refs) | 10-50 MB |
| `contact/contact_0.db` | Contact names, group membership, nicknames | 1-5 MB |
| `media/media_0.db` | Image / video / file metadata + thumbnails | 5-20 MB |

`vchat history "<群名>" -n 5000` reads `message_0.db` filtered by the
group's internal ID. The output is a tab-separated text stream:

```
2026-06-02 09:04:19  wxid_xxx  消息内容
2026-06-02 09:04:33  wxid_yyy  回复内容
...
```

**Real names vs wxid:** vchat resolves wxid → display name via `contact_0.db`,
but **the contact cache is often wrong** (it lags behind the actual WeChat
client's display name). If a name in `vchat history` looks off, ask the user
or cross-check with the chat log timestamps (e.g. "who said X at 14:22?").

### Windows encoding gotcha

PowerShell defaults to GBK (codepage 936). The chat log file is UTF-8
without BOM. If you read it via `Get-Content` directly you'll get mojibake.

```powershell
# Fix: set console encoding BEFORE redirecting
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
vchat history "群名" -n 5000 | Out-File -Encoding utf8 C:\tmp\chat_log.txt
```

In Git Bash / WSL on Windows, the default is already UTF-8 and there's
no fix needed.

## 2. Custom WeChat install path

vchat assumes WeChat is at `%USERPROFILE%\Documents\WeChat Files\` (Windows)
or `~/Library/Containers/com.tencent.xinWeChat/Data/...` (macOS).

If you installed WeChat somewhere else — say `D:\Apps\WeChat\` (a common
Chinese setup where the user keeps the OS drive small) — vchat can't
find the db_storage dir. The `vchat doctor` command will report
"found 0 db_storage" or similar.

**Fix:** set the `WECHAT_INSTALL_DIR` environment variable to your
WeChat install root.

```powershell
# PowerShell (persistent for current user)
[System.Environment]::SetEnvironmentVariable(
    "WECHAT_INSTALL_DIR", "D:\Apps\WeChat", "User"
)

# Then restart your shell, re-run:
vchat doctor
```

vchat will look for `<WECHAT_INSTALL_DIR>/WeChat Files/<wxid>/db_storage/`
and `<WECHAT_INSTALL_DIR>/xwechat_files/<wxid>/db_storage/`.

## 3. V2 .dat image attachments

V2 .dat files (the `Img/<YYYY-MM>/<hash>.dat` files under
`db_storage/hardlink/` and the real `msg/attach/<...>/Img/<YYYY-MM>/`
storage) are AES-128-ECB encrypted. Each file's first 15 bytes are
random header bytes; bytes 15..31 are the first ciphertext block.

The 16-byte AES key is held in the WeChat process memory and refreshed
on each app start. To extract it:

### macOS / Linux

```bash
vchat setup     # if not already
# vchat internally runs the C-based find_keys_macos
# writes ~/.vchat/data/config.json with image_aes_key
```

### Windows

There's no vchat-native Windows tool (as of vantasma-toolkit 2026-06).
We provide `scripts/find_image_key_windows.py` which:

1. Enumerates processes for `WeChat.exe` (legacy) or `Weixin.exe` (4.x+).
2. Opens the process with `PROCESS_VM_READ | PROCESS_QUERY_INFORMATION`.
3. Walks readable memory regions via `VirtualQueryEx`.
4. For each 16-byte aligned position, attempts AES-128-ECB decryption of
   a known first ciphertext block and checks if the plaintext starts with
   an image magic (`89 50 4E 47 0D 0A 1A 0A` for PNG, `FF D8 FF E0/E1`
   for JPEG, `47 49 46 38` for GIF, `52 49 46 46 ... 57 45 42 50` for WebP).
5. Cross-validates by trying to decrypt **all** sample .dat files in the
   target date's Img/ directory and confirming only one key works.
6. Writes the key to `~/.vchat/data/config.json`.

Expected runtime: ~30-60 seconds for a 100-200 MB WeChat process.

```powershell
python scripts/find_image_key_windows.py
# Output (your pid / scanned size / key will differ):
#   WeChat pid: 12345
#   Scanned 152.3 MB across 87 regions
#   Found AES key: <32 hex chars>
#   Wrote to C:\Users\<you>\.vchat\data\config.json
```

Then decrypt images (read the key back from `~/.vchat/data/config.json`):

```python
import json
from pathlib import Path
from vchat_core.image_codec import v2_decrypt

CFG = json.loads(Path.home().joinpath(".vchat/data/config.json").read_text())
KEY = bytes.fromhex(CFG["image_aes_key"])
SRC = Path(os.environ["WECHAT_INSTALL_DIR"]) / "xwechat_files" / "<wxid>" / "msg" / "attach" / "<hash>" / "2026-06" / "Img"
DST = Path("./imgs_2026-06-02")
DST.mkdir(exist_ok=True)

for dat in SRC.glob("*.dat"):
    out = v2_decrypt(dat.read_bytes(), KEY)
    (DST / (dat.stem + _ext_of(out))).write_bytes(out)
```

> **Image understanding is out of scope.** The decrypted images are
> written to disk; what they *mean* is up to you (or a human, or a
> vision model that isn't currently flaky). Do not auto-caption them
> in the rendered daily.

## 4. Group members (for avatar card rendering)

`vchat group-members --avatars "<群名>"` exports each group member's
wxid, display name, and avatar (small base64 JPEG) as JSON.

The avatar list is needed by the mobile renderer to put faces on
the cast cards. If the contact cache has wrong names (it usually does
for non-default accounts), the AI writer should ask the user for the
real name → wxid → nickname mapping before composing the daily.
