#!/usr/bin/env python3
"""群日报·手机版 v3.0 渲染器。

900px 宽单列卡片流。日报骨架 + 锐评 + 卡片化（中锐评）。

设计哲学：
- 保留日报骨架：朱砂红/深蓝/黑/米白配色，宋体/黑体/Playfair Display
- 锐评化调味：栏目名锐评化，朱砂红加重，锐评角标，个别黑色幽默图标
- 卡片化升级：圆角 + 阴影，章节之间大空白，满宽图片，放大头像

输入：
  story.json      # group-daily skill 产出
  avatars.json    # 头像 base64 映射
  plan-mobile.json  # 卡片数组 + 报头字段
  <out.html>

输出：
  HTML 文件（900px 宽单列卡片流，长度自适应）

用法：
  python3 render_mobile.py story.json avatars.json plan.json out.html
"""
import html
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image
    _has_pil = True
except ImportError:
    _has_pil = False


# ============== 工具函数 ==============
def h(s):
    return html.escape(str(s)) if s is not None else ""


def avatar(name, wxid, avatars, size=64, cls="avatar"):
    """生成头像 HTML（找不到头像用首字 placeholder）。"""
    src = avatars.get(name, "") or avatars.get(wxid or "", "")
    if src:
        return (f'<img class="{cls}" src="{src}" alt="{h(name)}" '
                f'style="width:{size}px;height:{size}px;border-radius:50%;" />')
    first = name[0] if name else "·"
    font_size = max(10, int(size * 0.42))
    return (f'<span class="{cls} avatar-text" '
            f'style="width:{size}px;height:{size}px;line-height:{size}px;'
            f'font-size:{font_size}px;border-radius:50%;">'
            f'{h(first)}</span>')


def auto_img_style(image_path, target_width_px=None, max_height_px=None):
    """按图实际比例注入 inline style（防止变形）。"""
    if not _has_pil or not image_path or not image_path.startswith('file://'):
        return ''
    p = image_path.replace('file://', '')
    try:
        with Image.open(p) as img:
            w, h_img = img.size
    except Exception:
        return ''
    aspect = w / h_img if h_img else 1
    if target_width_px:
        disp_w = target_width_px
        disp_h = int(disp_w / aspect)
        if max_height_px and disp_h > max_height_px:
            disp_h = max_height_px
            disp_w = int(disp_h * aspect)
        return f'width:{disp_w}px;height:{disp_h}px;object-fit:cover;'
    return ''


# ============== 卡片渲染器 ==============
def render_card_lead(story, avatars, plan_card):
    """头条卡（开屏大字+opening）—— 深蓝底白字，制造"重要"感。"""
    date = story.get("date", "")
    weekday_map = {1: "周一", 2: "周二", 3: "周三", 4: "周四", 5: "周五",
                   6: "周六", 7: "周日"}
    try:
        wd = weekday_map[datetime.strptime(date, "%Y-%m-%d").isoweekday()]
    except Exception:
        wd = ""
    opening = plan_card.get("opening") or story.get("opening", "")
    lead_title = plan_card.get("lead_title") or story.get("lead_title", "")
    kicker = plan_card.get("kicker", "头 版 锐 评 · 今日最扎心")
    masthead = plan_card.get("masthead", {})

    return f"""
<section class="card card-lead">
  <div class="card-eyebrow">📢 {h(kicker)}</div>
  <h1 class="lead-title">{lead_title.replace(chr(10), '<br>')}</h1>
  <div class="lead-meta">
    <span>{h(date)}</span>
    <span>{h(wd)}</span>
    <span>{h(masthead.get('issue_no',''))}</span>
  </div>
  <p class="lead-opening">{h(opening)}</p>
</section>
"""


def render_card_hero(story, avatars, plan_card, card_idx=0):
    """主稿卡（带图/不带图）—— 卡片化主稿。"""
    h_p = plan_card.get("hero", {})
    cast = h_p.get("cast", [])
    cast_html = "".join(
        f'<span class="cast-chip">{avatar(c["name"], c.get("wxid",""), avatars, size=44)}'
        f'<span class="cast-name">{h(c["name"])}</span></span>'
        for c in cast
    )
    body = h_p.get("body", "")
    body_html = ""
    if body:
        # 按 \n\n 拆段（支持多段叙事）
        paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
        body_html = "".join(f"<p>{h(p)}</p>" for p in paragraphs)
    quotes = h_p.get("quotes", [])
    quotes_html = "".join(
        f'<div class="quote">"{h(q["text"])}"'
        f'<span class="who">— {h(q["who"])}</span></div>'
        for q in quotes
    )
    image = h_p.get("image", "")
    img_html = ""
    if image:
        img_style = auto_img_style(image, target_width_px=820, max_height_px=520)
        img_html = f"""
<figure class="hero-figure">
  <img src="{h(image)}" alt="{h(h_p.get('image_alt',''))}" style="{h(img_style)}" />
  <figcaption>{h(h_p.get('image_caption',''))}</figcaption>
</figure>
"""
    produced = h_p.get("produced_html", "")
    return f"""
<section class="card card-hero">
  <div class="hero-eyebrow">{h(h_p.get('eyebrow', '锐 评 · RUI PING'))}</div>
  <h2 class="hero-title">{h_p.get('title_html', '')}</h2>
  <div class="hero-meta">
    <span class="time">{h(h_p.get('time', ''))}</span>
    <span class="badge">{h(h_p.get('badge', ''))}</span>
  </div>
  <div class="hero-cast">{cast_html}</div>
  {img_html}
  <div class="hero-body">
    {body_html}
  </div>
  <div class="hero-quotes">
    {quotes_html}
  </div>
  <div class="hero-produced">{produced}</div>
</section>
"""


def render_card_timeline(story, avatars, plan_card):
    """时间线卡（手机竖向时间轴）—— 锐评化：抗压实录。"""
    items = plan_card.get("items", [])
    items_html = "".join(
        f"""
<div class="tl-item">
  <div class="tl-time">{h(it.get('time',''))}</div>
  <div class="tl-dot"></div>
  <div class="tl-content">
    <div class="tl-text">{h(it.get('text',''))}</div>
    <div class="tl-who">— {h(it.get('who',''))}</div>
  </div>
</div>
"""
        for it in items
    )
    return f"""
<section class="card card-timeline">
  <div class="card-banner timeline-banner">⏱ {h(plan_card.get('banner','今 日 抗 压 实 录 · 时 间 线'))}</div>
  <div class="tl-list">
    {items_html}
  </div>
</section>
"""


def render_card_cast(story, avatars, plan_card):
    """人物高光卡（锐评化：今日主演）—— 单列大头像。"""
    items = plan_card.get("items", [])
    items_html = "".join(
        f"""
<div class="cast-item">
  {avatar(it["name"], it.get("wxid",""), avatars, size=72)}
  <div class="cast-info">
    <div class="cast-name">{h(it['name'])}</div>
    <div class="cast-tag">{h(it.get('tag',''))}</div>
    <div class="cast-desc">{h(it.get('desc',''))}</div>
  </div>
</div>
"""
        for it in items
    )
    return f"""
<section class="card card-cast">
  <div class="card-banner cast-banner">🎭 {h(plan_card.get('banner','今 日 主 演 · 8 位 扛 起 这 一 天 的 人'))}</div>
  <div class="cast-list">
    {items_html}
  </div>
</section>
"""


def render_card_stats(story, avatars, plan_card):
    """数字条卡（锐评化：今日高压指数）—— 黑底金字。"""
    items = plan_card.get("items", [])
    items_html = "".join(
        f'<div class="stat-item"><div class="n">{h(it.get("n",""))}</div>'
        f'<div class="l">{h(it.get("l",""))}</div></div>'
        for it in items
    )
    return f"""
<section class="card card-stats">
  <div class="card-banner stats-banner">💀 {h(plan_card.get('banner','今 日 高 压 指 数 · BY THE NUMBERS'))}</div>
  <div class="stats-grid">
    {items_html}
  </div>
</section>
"""


def render_card_quotes(story, avatars, plan_card):
    """金句墙卡（锐评化：锐评金句墙）—— 深蓝 banner。"""
    items = plan_card.get("items", [])
    items_html = "".join(
        f"""
<blockquote class="qw-item">
  <div class="qw-text">"{h(it.get('t',''))}"</div>
  <cite>— {h(it.get('cite',''))}</cite>
</blockquote>
"""
        for it in items
    )
    return f"""
<section class="card card-quotes">
  <div class="card-banner quotes-banner">💬 {h(plan_card.get('banner','锐 评 金 句 墙 · TODAY\'S VOICES'))}</div>
  <div class="qw-list">
    {items_html}
  </div>
</section>
"""


def render_card_lingo(story, avatars, plan_card):
    """黑话卡（锐评化：圈内黑话）—— 朱砂红 banner。"""
    items = plan_card.get("items", [])
    items_html = "".join(
        f'<div class="lingo-item"><div class="w">{h(it.get("w",""))}</div>'
        f'<div class="d">{h(it.get("d",""))}</div></div>'
        for it in items
    )
    return f"""
<section class="card card-lingo">
  <div class="card-banner lingo-banner">🔥 {h(plan_card.get('banner','圈 内 黑 话 · TODAY\'S LINGO'))}</div>
  <div class="lingo-grid">
    {items_html}
  </div>
</section>
"""


def render_card_tomorrow(story, avatars, plan_card):
    """明日预告卡（锐评化：ICU 通道）—— 深蓝 banner。"""
    items = plan_card.get("items", [])
    items_html = "".join(
        f"""
<div class="tm-item">
  <div class="tm-tag">{h(it.get('tag',''))}</div>
  <div class="tm-title">{h(it.get('title',''))}</div>
  <div class="tm-desc">{h(it.get('desc',''))}</div>
</div>
"""
        for it in items
    )
    qr = plan_card.get("qr", {})
    qr_html = ""
    if qr and qr.get("image"):
        qr_html = f"""
<figure class="tm-qr">
  <img src="{h(qr['image'])}" alt="{h(qr.get('alt',''))}" />
  <figcaption>
    <div class="qr-title">{h(qr.get('title',''))}</div>
    <div class="qr-desc">{h(qr.get('desc',''))}</div>
  </figcaption>
</figure>
"""
    return f"""
<section class="card card-tomorrow">
  <div class="card-banner tomorrow-banner">⏭ {h(plan_card.get('banner','明 日 预 告 · ICU 通 道'))}</div>
  <div class="tm-grid">
    <div class="tm-list">
      {items_html}
    </div>
    {qr_html}
  </div>
</section>
"""


def render_card_footer(story, avatars, plan_card):
    """报尾卡 —— 黑底金红字。"""
    stats = story.get("stats", {})
    fq = story.get("footer_quote", {})
    group = story.get("group_name", "")
    date = story.get("date", "")

    total_chars = stats.get('total_chars', 0)
    total_chars_fmt = f"{total_chars:,}" if isinstance(total_chars, int) else str(total_chars)

    fq_text = fq.get("text", "")
    # 中锐评：报尾收尾句如果太"文绉绉"，可以加一句
    return f"""
<section class="card card-footer">
  <div class="footer-stats">
    <div class="stat"><div class="n">{h(stats.get('total_messages','—'))}</div><div class="l">Messages</div></div>
    <div class="stat"><div class="n">{h(stats.get('unique_senders','—'))}</div><div class="l">People</div></div>
    <div class="stat"><div class="n">{total_chars_fmt}</div><div class="l">Characters</div></div>
    <div class="stat"><div class="n">{len(story.get('timeline',[]))}</div><div class="l">Stories</div></div>
    <div class="stat"><div class="n">+{h(stats.get('new_members',0))}</div><div class="l">Newcomer</div></div>
  </div>
  <div class="footer-quote">
    <div class="t">"{h(fq_text)}"</div>
    <div class="a">— {h(fq.get('attr',''))}</div>
  </div>
  <div class="footer-meta">
    <span>{h(group)} · {h(date)}</span>
    <span>{h(story.get('time_range',''))}</span>
    <span>本期完 · 明日续（如果有命的话）</span>
  </div>
</section>
"""


# 卡片模板路由
CARD_RENDERERS = {
    "lead": render_card_lead,
    "hero": render_card_hero,
    "timeline": render_card_timeline,
    "cast": render_card_cast,
    "stats": render_card_stats,
    "quotes": render_card_quotes,
    "lingo": render_card_lingo,
    "tomorrow": render_card_tomorrow,
    "footer": render_card_footer,
}


# ============== CSS（手机版·日报骨架+锐评+卡片化） ==============
CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;700;900&family=Noto+Sans+SC:wght@400;700;900&family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400&family=Old+Standard+TT:wght@400;700&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }

html, body {
  background: #2a241c;
  font-family: "Noto Serif SC", "Songti SC", "STSong", serif;
  color: #000;
  font-size: 16px;
  line-height: 1.7;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px 0;
  min-height: 100vh;
}

.page {
  width: 900px;
  background: #fdfcf8;
  margin: 0;
  box-shadow: 0 8px 40px rgba(0,0,0,0.25);
}

/* 报头 */
.card-masthead {
  background: #fdfcf8;
  padding: 36px 40px 28px;
  border-bottom: 2px solid #000;
  text-align: center;
}
.mh-name {
  font-family: "Noto Serif SC", "Songti SC", serif;
  font-weight: 900;
  color: #c41e1e;
  font-size: 64px;
  letter-spacing: 4px;
  line-height: 1.1;
  margin-bottom: 8px;
}
.mh-name .name-bot {
  display: block;
  font-size: 48px;
  margin-top: 4px;
  letter-spacing: 6px;
}
.mh-pinyin {
  font-family: "Playfair Display", "Old Standard TT", serif;
  font-size: 13px;
  letter-spacing: 4px;
  color: #c41e1e;
  font-weight: 700;
  margin-bottom: 14px;
  text-transform: uppercase;
}
.mh-meta {
  font-family: "Old Standard TT", serif;
  font-size: 11px;
  letter-spacing: 2px;
  color: #555;
  text-transform: uppercase;
  line-height: 1.7;
  margin-bottom: 8px;
}
.mh-slogan {
  font-family: "Songti SC", "Noto Serif SC", serif;
  font-size: 15px;
  letter-spacing: 3px;
  color: #222;
  font-weight: 700;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid rgba(0,0,0,0.5);
  line-height: 1.5;
}

/* 通用卡片 */
.card {
  margin: 24px;
  background: #fdfcf8;
  border: 1.5px solid #000;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  overflow: hidden;
  position: relative;
}

.card-banner {
  background: #c41e1e;
  color: #fdfcf8;
  font-family: "Noto Sans SC", "PingFang SC", "Heiti SC", sans-serif;
  font-size: 16px;
  font-weight: 900;
  letter-spacing: 3px;
  text-align: center;
  padding: 12px 0;
  border-bottom: 1.5px solid #000;
}

/* 头条卡（深蓝底白字，重要感） */
.card-lead {
  padding: 32px 40px;
  background: #1f2d4a;
  color: #fdfcf8;
  border-color: #1f2d4a;
}
.card-eyebrow {
  font-family: "Noto Sans SC", sans-serif;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 4px;
  color: #c41e1e;
  margin-bottom: 14px;
  text-transform: uppercase;
}
.lead-title {
  font-family: "Noto Serif SC", "Songti SC", serif;
  font-weight: 900;
  font-size: 44px;
  letter-spacing: 2px;
  line-height: 1.22;
  margin-bottom: 16px;
  color: #fdfcf8;
}
.lead-meta {
  font-family: "Old Standard TT", serif;
  font-size: 12px;
  letter-spacing: 2px;
  color: rgba(253,252,248,0.7);
  margin-bottom: 18px;
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}
.lead-opening {
  font-family: "Noto Serif SC", "Songti SC", serif;
  font-size: 17px;
  line-height: 1.85;
  color: rgba(253,252,248,0.95);
}

/* 主稿卡 */
.card-hero {
  padding: 28px 36px;
}
.hero-eyebrow {
  font-family: "Old Standard TT", serif;
  font-size: 12px;
  letter-spacing: 5px;
  color: #c41e1e;
  font-weight: 700;
  text-transform: uppercase;
  margin-bottom: 10px;
}
.hero-title {
  font-family: "Songti SC", "Noto Serif SC", serif;
  font-size: 32px;
  font-weight: 900;
  letter-spacing: 2px;
  line-height: 1.25;
  margin-bottom: 12px;
  color: #000;
}
.hero-title .deck {
  display: block;
  font-family: "Songti SC", serif;
  font-style: italic;
  font-weight: 400;
  font-size: 18px;
  letter-spacing: 1.5px;
  line-height: 1.45;
  color: #555;
  margin-top: 6px;
}
.hero-meta {
  font-family: "Old Standard TT", serif;
  font-size: 12px;
  letter-spacing: 2px;
  color: #333;
  padding: 8px 0;
  border-top: 1px solid rgba(0,0,0,0.6);
  border-bottom: 1px solid rgba(0,0,0,0.6);
  display: flex;
  gap: 18px;
  margin-bottom: 14px;
}
.hero-meta .time { font-weight: 700; }
.hero-meta .badge { color: #c41e1e; font-weight: 700; }
.hero-cast {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 18px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(0,0,0,0.2);
  margin-bottom: 16px;
}
.cast-chip {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-family: "Songti SC", serif;
  font-size: 14px;
  font-weight: 700;
  color: #c41e1e;
  letter-spacing: 0.5px;
}
.cast-chip .avatar {
  border-radius: 50%;
  border: 1.5px solid #000;
  object-fit: cover;
}
.avatar-text {
  display: inline-block;
  text-align: center;
  background: #fdfcf8;
  border: 1.5px solid #000;
  font-family: "Songti SC", serif;
  color: #000;
  font-weight: 700;
}
.hero-figure {
  margin: 16px 0;
}
.hero-figure img {
  width: 100%;
  display: block;
  border: 1.5px solid #000;
  border-radius: 4px;
}
.hero-figure figcaption {
  font-family: "Songti SC", serif;
  font-size: 13px;
  line-height: 1.55;
  color: #555;
  text-align: center;
  margin-top: 8px;
  font-style: italic;
}
.hero-body {
  font-family: "Noto Serif SC", "Songti SC", serif;
  font-size: 16px;
  line-height: 1.85;
  color: #000;
  margin-bottom: 16px;
}
.hero-body p {
  text-indent: 2em;
  margin-bottom: 10px;
}
.hero-body p::first-letter {
  font-size: 30px;
  font-family: "Songti SC", serif;
  font-weight: 900;
  color: #c41e1e;
  margin-right: 4px;
  line-height: 1;
}
.hero-quotes {
  margin: 16px 0;
  padding: 16px 20px;
  border-left: 3px solid #c41e1e;
  background: rgba(196,30,30,0.04);
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.hero-quotes .quote {
  font-family: "Songti SC", "Noto Serif SC", serif;
  font-size: 16px;
  line-height: 1.6;
  font-style: italic;
  color: #000;
}
.hero-quotes .who {
  font-family: "Old Standard TT", serif;
  font-size: 12px;
  font-style: normal;
  color: #c41e1e;
  font-weight: 700;
  margin-left: 4px;
}
.hero-produced {
  font-family: "Songti SC", serif;
  font-size: 14px;
  line-height: 1.6;
  letter-spacing: 0.5px;
  padding: 12px 0;
  border-top: 2px solid #c41e1e;
  border-bottom: 2px solid #c41e1e;
  color: #000;
  margin-top: 8px;
}
.hero-produced b { color: #c41e1e; letter-spacing: 2px; }

/* 时间线卡 */
.card-timeline {
  padding: 0;
}
.timeline-banner {
  border-radius: 8px 8px 0 0;
}
.tl-list {
  padding: 24px 36px 24px;
}
.tl-item {
  display: grid;
  grid-template-columns: 80px 20px 1fr;
  gap: 14px;
  margin-bottom: 18px;
  align-items: start;
}
.tl-item:last-child { margin-bottom: 0; }
.tl-time {
  font-family: "Playfair Display", serif;
  font-size: 20px;
  font-weight: 900;
  color: #c41e1e;
  letter-spacing: 1px;
  text-align: right;
  line-height: 1.2;
}
.tl-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #c41e1e;
  border: 2px solid #fdfcf8;
  box-shadow: 0 0 0 1.5px #c41e1e;
  margin-top: 6px;
  justify-self: center;
}
.tl-text {
  font-family: "Noto Serif SC", "Songti SC", serif;
  font-size: 16px;
  line-height: 1.7;
  color: #000;
  margin-bottom: 4px;
}
.tl-who {
  font-family: "Songti SC", serif;
  font-size: 12px;
  color: #555;
  font-style: italic;
  letter-spacing: 0.5px;
}

/* 人物卡 */
.card-cast {
  padding: 0;
}
.cast-banner {
  border-radius: 8px 8px 0 0;
}
.cast-list {
  padding: 24px 36px;
  display: flex;
  flex-direction: column;
  gap: 0;
}
.cast-item {
  display: grid;
  grid-template-columns: 72px 1fr;
  gap: 18px;
  align-items: flex-start;
  padding: 16px 0;
  border-bottom: 1px solid rgba(0,0,0,0.15);
}
.cast-item:last-child { border-bottom: none; }
.cast-item .avatar {
  border-radius: 50%;
  border: 1.5px solid #000;
  object-fit: cover;
}
.cast-info { display: flex; flex-direction: column; gap: 4px; }
.cast-name {
  font-family: "Noto Sans SC", "PingFang SC", sans-serif;
  font-size: 19px;
  font-weight: 900;
  letter-spacing: 1px;
  color: #000;
}
.cast-tag {
  font-family: "Songti SC", serif;
  font-size: 13px;
  color: #c41e1e;
  font-weight: 700;
  letter-spacing: 0.5px;
}
.cast-desc {
  font-family: "Noto Serif SC", serif;
  font-size: 14px;
  line-height: 1.7;
  color: #222;
  margin-top: 4px;
}

/* 数字条卡 */
.card-stats {
  padding: 0;
}
.stats-banner {
  background: #000;
  border-radius: 8px 8px 0 0;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  padding: 20px 24px;
  gap: 8px;
  background: #fdfcf8;
}
.stat-item {
  text-align: center;
  border-right: 1px solid rgba(0,0,0,0.18);
  padding: 0 8px;
}
.stat-item:last-child { border-right: none; }
.stat-item .n {
  font-family: "Playfair Display", serif;
  font-size: 36px;
  font-weight: 900;
  line-height: 1;
  color: #c41e1e;
}
.stat-item .l {
  font-family: "Songti SC", serif;
  font-size: 12px;
  letter-spacing: 1.5px;
  color: #333;
  margin-top: 6px;
}

/* 金句墙卡 */
.card-quotes {
  padding: 0;
}
.quotes-banner {
  background: #1f2d4a;
  border-radius: 8px 8px 0 0;
}
.qw-list {
  padding: 24px 36px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.qw-item {
  border-left: 3px solid #c41e1e;
  padding: 4px 0 4px 18px;
  margin: 0;
}
.qw-text {
  font-family: "Noto Serif SC", "Songti SC", serif;
  font-size: 17px;
  line-height: 1.6;
  font-style: italic;
  color: #000;
  margin-bottom: 6px;
}
.qw-item cite {
  display: inline-block;
  font-family: "Old Standard TT", serif;
  font-style: normal;
  font-size: 12px;
  letter-spacing: 1.5px;
  color: #1f2d4a;
  font-weight: 700;
}

/* 黑话卡 */
.card-lingo {
  padding: 0;
}
.lingo-banner {
  border-radius: 8px 8px 0 0;
}
.lingo-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  padding: 24px 36px;
  gap: 18px 28px;
}
.lingo-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 0;
  border-bottom: 1px solid rgba(0,0,0,0.15);
}
.lingo-item .w {
  font-family: "Noto Sans SC", "PingFang SC", sans-serif;
  font-size: 19px;
  font-weight: 900;
  color: #c41e1e;
  letter-spacing: 1px;
  line-height: 1.2;
}
.lingo-item .d {
  font-family: "Noto Serif SC", serif;
  font-size: 13px;
  line-height: 1.65;
  color: #222;
}

/* 明日预告卡 */
.card-tomorrow {
  padding: 0;
}
.tomorrow-banner {
  background: #1f2d4a;
  border-radius: 8px 8px 0 0;
}
.tm-grid {
  display: grid;
  grid-template-columns: 1fr 200px;
  gap: 24px;
  padding: 24px 36px;
  align-items: start;
}
.tm-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}
.tm-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(0,0,0,0.15);
}
.tm-item:last-child { border-bottom: none; }
.tm-tag {
  font-family: "Old Standard TT", serif;
  font-size: 11px;
  letter-spacing: 2px;
  color: #c41e1e;
  font-weight: 700;
}
.tm-title {
  font-family: "Noto Sans SC", "PingFang SC", sans-serif;
  font-size: 17px;
  font-weight: 900;
  letter-spacing: 1px;
  line-height: 1.3;
  color: #000;
}
.tm-desc {
  font-family: "Noto Serif SC", serif;
  font-size: 14px;
  line-height: 1.7;
  color: #222;
}
.tm-qr {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  border: 1.5px solid #000;
  padding: 12px;
  background: #fdfcf8;
}
.tm-qr img {
  width: 100%;
  max-width: 160px;
  display: block;
  border: 1px solid #000;
}
.tm-qr .qr-title {
  font-family: "Noto Sans SC", sans-serif;
  font-size: 14px;
  font-weight: 900;
  letter-spacing: 1px;
  margin-top: 8px;
  color: #000;
}
.tm-qr .qr-desc {
  font-family: "Old Standard TT", serif;
  font-size: 11px;
  color: #555;
  margin-top: 4px;
  font-style: italic;
}

/* 报尾卡 */
.card-footer {
  background: #000;
  color: #fdfcf8;
  padding: 28px 36px;
  border-color: #000;
}
.footer-stats {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255,255,255,0.3);
  margin-bottom: 16px;
}
.footer-stats .stat {
  text-align: center;
}
.footer-stats .stat .n {
  font-family: "Playfair Display", serif;
  font-size: 28px;
  font-weight: 900;
  color: #c41e1e;
  line-height: 1;
}
.footer-stats .stat .l {
  font-family: "Old Standard TT", serif;
  font-size: 11px;
  letter-spacing: 1.5px;
  color: rgba(253,252,248,0.7);
  margin-top: 4px;
  text-transform: uppercase;
}
.footer-quote {
  text-align: center;
  padding: 16px 0;
  border-top: 1px solid rgba(255,255,255,0.2);
  border-bottom: 1px solid rgba(255,255,255,0.2);
  margin-bottom: 12px;
}
.footer-quote .t {
  font-family: "Songti SC", "Noto Serif SC", serif;
  font-size: 18px;
  font-style: italic;
  letter-spacing: 3px;
  line-height: 1.5;
  color: #fdfcf8;
}
.footer-quote .a {
  font-family: "Old Standard TT", serif;
  font-size: 12px;
  letter-spacing: 1.5px;
  color: #c41e1e;
  font-weight: 700;
  margin-top: 6px;
}
.footer-meta {
  display: flex;
  justify-content: space-between;
  font-family: "Old Standard TT", serif;
  font-size: 11px;
  letter-spacing: 1.5px;
  color: rgba(253,252,248,0.6);
  text-transform: uppercase;
  flex-wrap: wrap;
  gap: 8px;
}
"""


def render(story, avatars, plan):
    """渲染手机版日报。"""
    cards = plan.get("cards", [])
    masthead = plan.get("masthead", {})
    group = story.get("group_name", "")
    date = story.get("date", "")

    name_top = masthead.get('name_top', group) or group or "群"
    name_bot = masthead.get('name_bot', '日报') or "日报"
    pinyin = masthead.get('pinyin', 'DAILY · RUI PING')
    slogan = masthead.get('slogan_cn_html', '群 魂 · 共 建 · 共 学<br>抗 压 背 锅 · 今 日 实 录')
    cn_no = masthead.get('cn_no', '')
    issue_code = masthead.get('issue_code', '')
    issue_no = masthead.get('issue_no', '')
    lunar = masthead.get('lunar', '')
    publisher = masthead.get('publisher', f'{group}群出版')
    total_pages = masthead.get('total_pages', f'今日 {len(cards)+1} 卡')

    # 报头 HTML
    masthead_html = f"""
<section class="card-masthead">
  <h1 class="mh-name">{h(name_top)}<span class="name-bot">{h(name_bot)}</span></h1>
  <div class="mh-pinyin">{h(pinyin)}</div>
  <div class="mh-meta">
    <div>{h(cn_no)} · {h(issue_code)} · {h(issue_no)}</div>
    <div>{h(date)} · {h(lunar)} · {h(publisher)}</div>
    <div>{h(total_pages)}</div>
  </div>
  <div class="mh-slogan">{slogan}</div>
</section>
"""

    # 渲染所有 cards
    card_html_list = []
    for i, card in enumerate(cards):
        tpl = card.get("template", "hero")
        renderer = CARD_RENDERERS.get(tpl)
        if renderer:
            if tpl == "hero":
                card_html_list.append(renderer(story, avatars, card, i))
            else:
                card_html_list.append(renderer(story, avatars, card))
        else:
            # 未知模板：降级为 hero（用 card 自身字段作为 hero 输入）
            fallback = {"hero": card}
            card_html_list.append(render_card_hero(story, avatars, fallback, i))

    n = len(card_html_list)
    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=900, initial-scale=1">
<title>{h(group)} · {h(date)} · 手机版日报（共 {n} 卡）</title>
<style>
{CSS}
</style>
</head>
<body>
<div class="page">
  {masthead_html}
  {''.join(card_html_list)}
</div>
</body>
</html>
"""


def main():
    if len(sys.argv) < 5:
        print("Usage: render_mobile.py <story.json> <avatars.json> <plan.json> <out.html>")
        sys.exit(1)
    story = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    avatars = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    plan = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
    out_path = sys.argv[4]
    html_str = render(story, avatars, plan)
    Path(out_path).write_text(html_str, encoding="utf-8")
    print(f"[OK] Wrote {out_path} ({len(html_str)} bytes, {len(plan.get('cards',[]))} cards)")


if __name__ == "__main__":
    main()
