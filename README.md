# WeChat Group Daily · 微信群日报

> **把本地微信群某天的聊天记录，做成杂志风日报 HTML + 长图 PNG（手机 900px）或 A3 报纸版 PDF，并可自动发回群内。**
> 端到端：本地微信数据 → 解密 → 文案 → 渲染 → 自检 → 交付 → (可选) 自动发群。

> ⚠️ **免责声明 · Personal Learning Only**
>
> 本仓库所有内容**仅供个人学习与研究目的**。工具只在使用者**自己的设备 / 自己拥有合法访问权的数据**上操作。**严禁用于**：
>
> - 未经他人同意访问、解析他人账号或数据
> - 任何商业目的的批量采集、出售、转发
> - 监控、跟踪、骚扰他人
> - 违反《中华人民共和国网络安全法》《个人信息保护法》《数据安全法》以及微信、飞书等平台用户协议的任何行为
>
> 本工具不提供任何形式的明示或暗示担保。一切使用后果由使用者自行承担。
> **一旦下载或使用本仓库内容，即视为接受上述声明**。详见 [LICENSE](LICENSE) 的"附加条款"。



[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Platform: Windows / macOS / Linux](https://img.shields.io/badge/platform-Win%20%7C%20macOS%20%7C%20Linux-lightgrey)]()
[![vchat-powered](https://img.shields.io/badge/powered%20by-vchat-orange)](https://github.com/xiangruiai/vantasma-toolkit)
[![影刀 RPA](https://img.shields.io/badge/%E5%BD%B1%E5%88%80-RPA%20%E5%8F%AF%E9%80%89-blue)]()

---

## 🚀 5 分钟开始

> **三步跑通**——无需手敲命令，agent 帮你跑完所有事。

1. **复制仓库地址** → `https://github.com/chouxiangdick/wechat-group-daily`
2. **发给任意 agent**（Mavis / Claude / GPT / Cursor 都能接）
3. **说一句**：

   ```
   给 <群名> 做 <YYYY-MM-DD> 的日报
   ```

   或报纸版：

   ```
   给 <群名> 做 <YYYY-MM-DD> 的报纸版日报
   ```

**agent 收到后会自己跑的事**：

- [x] 检查微信已登录 + 找聊天文件夹路径
- [x] 装 vchat + 解密 db
- [x] 拉聊天记录 + 写日报文案
- [x] 渲染 HTML + 900px PNG 长图
- [x] 强制自检 4 项（日期 / 星期 / 农历 / 引用字面真实）
- [x] 输出到 `~/Desktop/<群名>_日报/`
- [ ] （可选）影刀 RPA 自动发到群里

> **触发关键词**：`做日报` / `做报纸` / `群日报` / `WeChat group daily`
> **前置要求**：桌面微信保持登录（agent 会自己检查）
> **默认风格**：🎭 **贴吧阴阳版**（嘴臭 · 反讽 · 黑色幽默 · 标题党）—— 适合 5-30 人小群、想发出去有人看的场景

---

---

## 三个版本（任选其一，不要混搭）

| 版本 | 谁来跑 | 何时跑 | 输出落点 | 自动发群？ | 状态 |
|---|---|---|---|---|---|
| **v1 基础版** | 你 + 任意 AI agent | 你说"做日报" | `~/Desktop/<群名>_日报/` | ❌ 手动发 | ✅ 跑通 |
| **v2 进阶版** | agent + [影刀 RPA](https://www.yingdao.com/) | 你说"做日报" + RPA 监听文件夹 | 同上 + 微信群里一张图 | ✅ 自动 | ✅ 跑通 |
| **v3 无人值守**（Roadmap）| 定时任务 + agent + 影刀 RPA | 每天定时，无需人工 | 自动日报 + 自动发群 | ✅ 自动 | ⚠️ **未测试，仅方案** |

> **怎么选**：先 v1 跑通 → 再加 v2 → v3 是未来。**v3 不要直接上生产**。

---

## 🎨 风格档位（3 选 1，默认贴吧版）

| 风格 | 适合场景 | 触发词 | 调性关键词 |
|---|---|---|---|
| 🎭 **贴吧阴阳版**（默认）| 小群自嘲、想发出去有人看 | `"做贴吧版日报"` 或 不加词（默认）| 嘴臭 / 反讽 / 标题党 / 黑色幽默 / 锐评金句 |
| 📰 **严肃日报版** | 给上级/合作方看、公开分享 | `"做严肃版日报"` 或 `"做纪要版"` | 客观 / 中性 / 数据 / 引语 / 排版严谨 |
| 💼 **商务金句版** | 群里有行业人脉/老板、想留个好印象 | `"做商务版日报"` 或 `"做行业版"` | 洞察 / 数字 / 行业术语 / 价值密度 |

**示例**（同一事件，3 种风格对比）：

> 🎭 **贴吧版**：「<外号 A> 一上午连发 4 条 key，<外号 B> 32 分钟配 API 没通——结论是 SDK 路径写的是 linux-x64，Windows 用户集体白干。」
>
> 📰 **严肃版**：「<真名 A> 于 09:04 发布升级邀请码，<真名 B> 尝试 32 分钟仍未配置成功。问题定位：SDK 路径不匹配 Windows 系统。」
>
> 💼 **商务版**：「群内 6 名成员当日获得体验资格，1 名成功接入，平均接入时长 32 分钟。Windows 平台兼容性是主要摩擦点。」

**风格怎么调**（2 种方式）：

1. **触发词（推荐）**：跟 agent 说时**带上风格词**
   ```
   给 <群名> 做 <日期> 的贴吧版日报
   给 <群名> 做 <日期> 的严肃版日报
   给 <群名> 做 <日期> 的商务版日报
   ```

2. **改 SKILL.md 配置（永久）**：编辑本仓库 `SKILL.md` 顶部的 `default_style` 字段：
   ```yaml
   ---
   name: wechat-group-daily
   default_style: tieba_yin_yang   # 可选: tieba_yin_yang / serious_news / business
   ---
   ```

> 💡 **风格混搭**：报纸版（`做报纸版`）默认走贴吧阴阳风；想报纸版严肃可以说 `"做严肃版报纸"`。

---

## 通用前置条件（三个版本都要先做）

> ⚠️ **agent 第一件事：跟用户确认以下 4 项。** 缺一项后续必卡。

### 1. Python 3.9+

```bash
python3 --version    # 应 ≥ 3.9
```

### 2. 桌面微信**正在运行 + 已登录**

**agent 必检**（Windows / macOS / Linux 都跑这条）：

```bash
# Windows PowerShell
Get-Process -Name WeChat,Weixin -ErrorAction SilentlyContinue | Select-Object Name,Id,MainWindowTitle

# macOS / Linux
pgrep -l -i 'wechat|weixin'
```

**预期输出**：进程存在 + `MainWindowTitle` 含"微信"。如果**没在跑**或**没登录** → **先告诉用户手动启动并扫码登录**，agent 不要自动绕过。

### 3. 微信聊天文件夹的位置（4 种找法，按顺序试）

| 优先级 | 路径 | 适用 |
|---|---|---|
| 默认 | `~/Documents/WeChat Files/<wxid>/` | Windows 微信默认安装 |
| 默认 2 | `~/Documents/xwechat_files/<wxid>/` | 微信 4.x 新版 |
| 自定义 | `<WECHAT_INSTALL_DIR>/WeChat Files/<wxid>/` | 微信装在非默认盘（D 盘等） |
| macOS | `~/Library/Containers/com.tencent.xinWeChat/Data/.../<wxid>/` | macOS |

**怎么告诉 agent**（任选一种）：

```powershell
# 方案 A：直接告诉 agent 路径（最稳）
"我的微信聊天文件夹是 <WECHAT_INSTALL_DIR>/xwechat_files/<你的 wxid>"

# 方案 B：让 agent 自己探（agent 会列几个候选让你确认）
"帮我找下微信聊天文件夹在哪"
```

**agent 必做的事**：把路径存成环境变量 `WECHAT_INSTALL_DIR`（或直接当参数传给 vchat）。

```powershell
[System.Environment]::SetEnvironmentVariable("WECHAT_INSTALL_DIR", "D:\Apps\WeChat", "User")
```

### 4. Chrome / Edge（HTML→PNG 截屏用）

```bash
google-chrome --version    # 或 msedge --version
```

---

## v1 基础版：跟着 agent 跑

### 1.1 一键装 vchat

> **agent 第一步** 一定是跑这条。**带超时 600 秒**；超时立刻停，问用户。

```bash
git clone https://github.com/<your-username>/wechat-group-daily.git
cd wechat-group-daily
bash scripts/vchat_setup.sh
```

**预期输出**：
```
==> vchat version
vchat 0.x.x
```

### 1.2 跑 setup + 验证 db 全部解密

```bash
# macOS / Linux
sudo vchat setup
vchat doctor

# Windows PowerShell
vchat setup
vchat doctor
```

**预期输出**（vchat doctor）：
```
✓ Found 18 db files, all decrypted
```

**如果输出 0 db** → 99% 是微信聊天文件夹路径不对 → 回"通用前置条件 3"。

### 1.3 找图片 AES key（Windows 必跑，macOS 跳过）

> ⚠️ 这一步需要微信进程在跑，agent 必先确认。

```powershell
# Windows
python scripts/find_image_key_windows.py
```

**预期输出**：
```
WeChat pid: 12345
Scanned 152.3 MB across 87 regions
Found AES key: <32 hex chars>
Wrote to ~/.vchat/data/config.json
```

### 1.4 拉聊天记录

```bash
# Windows PowerShell（必须先设 UTF-8 防乱码）
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
vchat history "<群名>" -n 5000 > /tmp/chat_log_<YYYY-MM-DD>_<群名>.txt

# macOS / Linux
vchat history "<群名>" -n 5000 > /tmp/chat_log_<YYYY-MM-DD>_<群名>.txt
```

**预期输出**：UTF-8 文本文件，含日期/时间/wxid/消息。

### 1.5 跟 agent 说一句话

```
"给 <群名> 做 <YYYY-MM-DD> 的日报，嘴臭版"
# 或
"给 <群名> 做 <YYYY-MM-DD> 的报纸版"     # → A3 PDF
```

**agent 会自己跑剩下的事**：写 story.json → 渲染 HTML → 截 PNG → 自检 → 交付。

### 1.6 拿到日报

输出落点：
- **Windows**：`C:\Users\<你>\Desktop\<群名>_日报\群日报_<群名>_<日期>_手机版.{html,png}`
- **macOS / Linux**：`~/Desktop/<群名>_日报/...`

**自检必过项**（agent 必跑 verify_daily.py）：

```bash
python scripts/verify_daily.py \
  --date     <YYYY-MM-DD> \
  --weekday  <周X> \
  --chat-log /tmp/chat_log_<YYYY-MM-DD>_<群名>.txt \
  --story    /tmp/story_<YYYY-MM-DD>_<群名>.json
```

**预期输出**：
```
✓ Date matches
✓ Weekday matches
✓ Lunar date matches
✓ All quotes present verbatim
ALL CLEAN
```

**任何一项 ❌ → 修日报，不修工具。** 重跑直到 ALL CLEAN。

---

## v2 进阶版：v1 + 影刀 RPA 自动发群

> v1 跑通后再上 v2。**先在影刀里测试 flow，不行再回来调 agent。**

### 2.1 装影刀 + 准备

1. 下载安装 [影刀 RPA](https://www.yingdao.com/)（个人非商业版免费）
2. 桌面微信**保持登录 + 窗口开着**（RPA 要自动化点微信）

### 2.2 手搓 flow（影刀 .flow 是私有格式，本仓库不直接发布；按 12 步手搓最稳）

完整手搓指南见 [`references/yingdao-rpa-setup.md`](references/yingdao-rpa-setup.md)——含每一步的"元素定位怎么写 / 失败怎么排查 / 模拟真人开关在哪"。

### 2.3 配置计划任务（文件触发器）

影刀 RPA → 计划任务 → 新建 → **文件触发器**：

| 字段 | 填什么 |
|---|---|
| 名称 | `日报创建触发器` |
| 应用 | `影刀_发送日报`（你刚导入的） |
| 监控文件夹 | `C:\Users\<你>\Desktop\<群名>_日报` |
| 包含子路径 | ✅ |
| 监控事件 | ✅ 创建（其他不勾）|
| 文件/文件夹类型 | `群日报*.png` 或 `*.png` |

> 💡 **触发器原理**：v1 的日报 PNG 一落到这个目录，影刀自动启动 flow。

### 2.4 影刀 flow 12 步

```
1.  开启模拟真人操作（让微信不检测为机器人）
2.  运行或打开 <日报输出文件夹>          ← 确认日报在不在
3.  获取文件列表（按群日报*.png 过滤）
4.  将文件添加到剪切板
5.  点击元素：按钮_微信
6.  点击元素：按钮_进入微信
7.  获取窗口对象：标题=微信
8.  点击元素：列表项目_<群名>
9.  填写输入框：搜索框输入 <群名>
10. 点击元素：列表项目_<群名>_1   ← 搜索结果第一条
11. 键盘输入 ^V（粘贴剪切板）
12. 键盘输入 ENTER（发送图片）
```

### 2.5 测试一次

1. 跑一次 v1 完整流程（"做日报"）
2. 影刀应该**自动启动** flow
3. 微信窗口会被影刀接管，**鼠标会动**，**几秒后群里出现日报图**
4. 如果哪一步失败：影刀 → 运行日志 → 看哪步报红 → 修对应元素定位

### 2.6 输出

| 路径 | 内容 |
|---|---|
| `~/Desktop/<群名>_日报/` | v1 生成的 HTML + PNG + (A3 PDF) |
| 微信群 `<群名>` 里 | 一张日报 PNG（自动） |

---

## v3 无人值守（Roadmap，未测试）

> ⚠️ **未测试**。本节只是方案参考，不要直接当生产部署。

### 3.1 思路

每天 23:00 跑：
1. Windows 任务计划程序 → 触发 agent（v1 完整流程）
2. agent 输出 PNG 到固定目录
3. 影刀文件触发器（v2）→ 自动发群
4. 开机自启动 = 影刀 + 微信挂在启动项

### 3.2 需要的组件（未测）

| 组件 | 用途 | 状态 |
|---|---|---|
| Windows 任务计划程序 | 每天定时跑 agent 命令 | ❌ 没配 |
| 影刀"开机启动" | 系统启动后影刀自动运行 | ❌ 没测 |
| 微信"开机自动登录" | 跳过扫码 | ❌ 微信不原生支持 |
| agent CLI 模式 | 无头 agent 能跑 v1 | ❌ 没做 |

### 3.3 已知风险

- **微信不原生支持开机自动登录** → 需要用户**手动扫码一次**（如果用影刀做"自动点击登录"会很脆）
- **agent 跑失败** 没人看到 → 需要加通知（email / push）
- **影刀挂掉** → 需要监控

### 3.4 想试的 user

在 issues 提个 "v3 试一下" 标签，开个新分支一起搞。

---

## 故障排查

| 症状 | 原因 | 修复 |
|---|---|---|
| `vchat doctor` 0 db | 微信聊天文件夹路径不对 | 通用前置条件 3 重新设 `WECHAT_INSTALL_DIR` |
| `chat_log` 全是乱码 | PowerShell GBK | `[Console]::OutputEncoding = UTF8` 再 `vchat history` |
| `find_image_key_windows.py` 找不到 key | 微信没运行 | 启动 + 登录 + 重跑 |
| `verify_daily.py` 报 quote 找不到 | quote 不在 chat_log | 改日报，重跑 |
| `chrome headless` 崩 | 缺 chrome | 装 chrome 或传 `--executable-path` |
| **macOS** `vchat setup` 失败 | 没 sudo | `sudo vchat setup` |
| 影刀第 5 步找不到"按钮_微信" | 微信窗口不在前台 | 影刀运行前**手动把微信前置** |

---

## 隐私与脱敏（**必读**）

**绝对不要 `git add` 以下内容**（本仓库 `.gitignore` 已部分覆盖，**手动再确认**）：

- ❌ `story.json` / `plan.json`（含真名 / 外号 / 真实原话）
- ❌ `*.png` / `*.pdf`（日报成品，含群友头像 + 真名 + 群外号）
- ❌ `chat_log_*.txt`（聊天记录原文）
- ❌ `avatars.json`（群友头像 base64）
- ❌ `~/.vchat/data/config.json` 里的 `image_aes_key`
- ❌ 任何含 `WECHAT_INSTALL_DIR` 实际值、wxid、群名的本地配置

**只能 commit 到本仓库**：
- ✅ 代码、脚本、模板、文档
- ✅ `examples/*.template.json`（纯占位符）

---

## 文件结构

```
wechat-group-daily/
├── SKILL.md                          # Mavis agent 看的 6 步流程
├── README.md                         # 你正在看的
├── LICENSE                           # MIT
├── .gitignore
├── automation/                       # v2 影刀 RPA 手搓指南（不直接发布 .flow，JSON schema 不稳）
│   └── (见 references/yingdao-rpa-setup.md)
├── scripts/
│   ├── vchat_setup.sh                # 一键装 vchat
│   ├── patch_vchat_windows.py        # weixin.exe + WECHAT_INSTALL_DIR 兼容
│   ├── find_image_key_windows.py     # 扫 WeChat 内存找 AES key
│   ├── verify_daily.py               # 强制自检 4 项
│   ├── make_daily.py                 # 主编排
│   ├── render_html.py                # mobile 900px 渲染
│   ├── html_to_png.py                # chrome headless 截屏
│   └── render_newspaper_a3.py        # A3 PDF 报纸版
├── references/
│   ├── data-sources.md               # 微信数据来源 + Windows 路径坑
│   └── story-schema.md               # story.json 字段
└── examples/
    ├── plan.template.json            # mobile cards 数组模板
    └── story.template.json           # 完整 story 字段模板
```

---

## 致谢

### 参考 / Inspired by
- [【飞行社】我又开源了一个群报纸 skill，让你的微信群每天都能产出一份高质量的报纸](https://www.feishu.cn/community/prompts?id=7641507288469261242&from=ug_from_subscribe_update) — 本项目整体设计思路的源头（"群日报 skill" + agent + render 三段式）
- [vantasma-toolkit](https://github.com/xiangruiai/vantasma-toolkit) — 整套解密能力（V2 .dat 图片 AES-128-ECB、本地 SQLite db 解密、跨平台 find_keys）的源头

### 依赖 / Powered by
- [vantasma-toolkit](https://github.com/xiangruiai/vantasma-toolkit) — 解密能力的地基（`vchat` CLI）
- [影刀 RPA](https://www.yingdao.com/) — v2 自动发群的执行器
- [Mavis / MiniMax](https://github.com) — AI agent runtime

### 特别感谢
- 早期测试群（v1 → v4 跑通日报的迭代过程）

## License

MIT — see [LICENSE](LICENSE).
