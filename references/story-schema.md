# story.json schema

The writer (AI) reads the chat log + (optional) decrypted images and
produces a `story.json` describing the day's narrative. The renderer
then composes the final HTML.

All examples below use **placeholder names** (`<群名>`, `<真名>`, `<外号>`,
`<时间>`) — never copy real group / member data into the schema doc
or any committed file.

## Top-level shape

```json
{
  "meta":          { ... },
  "lead":          "...",
  "hero_timeline": [ ... ],
  "cast_cards":    [ ... ],
  "stats":         [ ... ],
  "quotes":        [ ... ],
  "lingo":         [ ... ],
  "qa":            [ ... ],
  "footer_quote":  "..."
}
```

## `meta`

| Field | Type | Required | Notes |
|---|---|---|---|
| `group_name` | string | yes | Display name (e.g. `"<群名>"`) |
| `date` | string (YYYY-MM-DD) | yes | |
| `weekday` | string | yes | One of 周一/周二/周三/周四/周五/周六/周日 |
| `lunar` | string | yes | E.g. `"<干支年X月X>"` — compute via `lunardate`, never hand-write |
| `total_messages` | int | yes | From chat log line count |
| `active_senders` | int | yes | Distinct wxid count |
| `mood` | string | no | 1-2 word tone (e.g. `"<情绪标签>"`) |

## `lead`

2-3 sentence opening that frames the day's *one* big story. Must
include a thesis, not a recap. Example shape:

```json
"lead": "<一句话主论点：今天群里的一个核心事件/反转>。<为什么这件事重要>。<群体的整体反应是 XX>。"
```

## `hero_timeline`

Array of 6-8 time-bracketed arcs. Each one tells one slice of the day.

```json
{
  "time":      "HH:MM — HH:MM",
  "title":     "<事件标题>",
  "cast":      ["<真名/外号>"],
  "narrative": "<1-3 句,语义深度,不只贴原文>",
  "mood":      "<情绪标签>"
}
```

- `narrative` should be 1-3 sentences, semantic depth, not raw paste.
- `cast` uses display names the user has confirmed (real names + optional group nicknames).
- For `cast` entries, prefer the **real WeChat display name** as the
  primary key; the group nickname (if any) is a separate field on the
  cast card, not the cast array.

## `cast_cards`

6-8 highlight cards. One per "today's main actor".

```json
{
  "name":     "<真实 WeChat 显示名>",
  "nickname": "<群内梗,可选,只本群使用>",
  "wxid":     "wxid_xxxxxxxx",
  "role":     "<今日角色>",
  "tagline":  "<一句吐槽>",
  "highlight": "<今天最代表TA的一件事,1-2 句>",
  "mood":     "<情绪>",
  "avatar_b64": "data:image/jpeg;base64,..."
}
```

- `name` is the real WeChat display name (verified by user).
- `nickname` is the group-internal slang, optional. **Use only with
  user's permission; do not leak across groups.**
- `wxid` is a generic placeholder here — in real use, fill the
  user's actual wxid (which is not sensitive; it's a public routing
  identifier inside WeChat's protocol).
- `avatar_b64` is a small (~10-30 KB) base64 JPEG from
  `vchat group-members --avatars`. **Do not commit avatars to a
  public repo** — they belong in a private output dir, not in the
  story.json that goes through git.

## `stats`

3-6 numerical highlights. Each one should be **verifiable** in the
chat log (you can grep for it).

```json
{
  "label":  "<维度>",
  "value":  "<数字+单位>",
  "note":   "<解释>"
}
```

## `quotes`

3-6 verbatim quotes. **Every quote must be 100% present in the chat
log file** — no merging, no typo fixes, no paraphrasing.

```json
{
  "who":   "<真名/外号>",
  "quote": "<必须 100% 出现在 chat_log 文件里,不改字不合并>",
  "context": "<时间+场景>"
}
```

The `verify_daily.py` script greps each `quote` against the chat
log and fails the build if any are missing or modified.

## `lingo`

3-9 in-group slang terms / acronyms / running gags. Each gets a
black-humor one-liner.

```json
{
  "term":  "<群内黑话/缩写/经典梗>",
  "explain": "<黑色幽默一行解释>",
  "tone":  "吐槽/致敬/科普"
}
```

## `qa`

0-3 Q&A pairs pulled from real exchanges in the chat.

```json
{
  "q": "<群里真问过的问题>",
  "a": "<真实回答 + 后续发展,1-2 句>"
}
```

## `footer_quote`

One closing line, usually the day's most absurd / most poetic /
most fitting sentence from the chat log.

```json
"footer_quote": "<一句最贴合今日气质的原话> —— <发言者>, <HH:MM>, <场景>。"
```

---

## Privacy & data hygiene

- **Never commit** a real `story.json` to a public repo. It contains
  real names, real nicknames, real quotes, and real avatars.
- Story files should live in a private output dir (`/tmp/`, `~/Desktop/`)
  and never enter the skill's git tree.
- The `examples/story.template.json` shipped with this skill is
  pure placeholders — copy it and fill in your real data only in
  a non-tracked location.
