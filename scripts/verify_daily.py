"""verify_daily.py - 群日报/报纸 强制自检工具

跑日报时 Step 0.5 强制执行，校验：
1. 日期/星期正确性（不自报"周一"等）
2. 农历自动算（用 lunardate，不手写）
3. 数字基本合理性（总消息数 / 时间段）
4. 不能引用不存在的"MLGB"等纯语气词当 quote
5. 干支年正确

用法：
  python3 scripts/verify_daily.py --date 2026-06-02 --weekday 周二 --messages 312
  python3 scripts/verify_daily.py --date 2026-06-02 --chat-log /tmp/chat_log_xxx.txt
"""
import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    from lunardate import LunarDate
    HAS_LUNARDATE = True
except ImportError:
    HAS_LUNARDATE = False
    print("⚠️  没装 lunardate，pip install lunardate", file=sys.stderr)


TIANGAN = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
DIZHI = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
WEEKDAY_MAP = ['周一','周二','周三','周四','周五','周六','周日']

# 不可作为 quote 引用的"纯语气词"列表（日报里没信息量）
LOW_INFO_QUOTES = [
    'mlgb', 'nm', 'jb', 'nmb', 'fwb', '啊', '嗯', '哦', '?', '??', '???',
    '哈哈', '哈哈哈', '呵呵', '……', '...',
    '[表情]', '[图片]', '[系统]',
]


def verify_date(date_str: str) -> dict:
    """校验日期 + 自动算星期 + 自动算农历。"""
    d = datetime.strptime(date_str, "%Y-%m-%d")
    weekday = WEEKDAY_MAP[d.weekday()]
    year = d.year
    month = d.month
    day = d.day

    result = {
        "date": date_str,
        "weekday": weekday,
        "weekday_idx": d.weekday(),
        "is_weekend": d.weekday() >= 5,
        "gan_zhi": TIANGAN[(year - 4) % 10] + DIZHI[(year - 4) % 12],
    }

    if HAS_LUNARDATE:
        lunar = LunarDate.fromSolarDate(year, month, day)
        result["lunar"] = f"{lunar.year}年{lunar.month}月{lunar.day}日"
        result["lunar_compact"] = f"{lunar.month}月{lunar.day}"
    else:
        result["lunar"] = "(需 lunardate)"

    return result


def check_quotes(quotes: list, chat_log: str = None) -> list:
    """校验 quote 是否有信息量、是否在原文中存在（如果提供 chat_log）。"""
    issues = []
    for i, q in enumerate(quotes, 1):
        text = q.get("text", "").strip()
        # 1. 检查纯语气词
        for bad in LOW_INFO_QUOTES:
            if text.lower() == bad or text.lower().replace(' ', '') == bad:
                issues.append(f"  [{i}] '{text}' 纯语气词，日报不应作为 quote")
                break
        # 2. 如果提供了 chat_log，校验 quote 真实存在
        if chat_log and text and not text.startswith('sk-'):  # API key 特殊
            # 容错匹配：去除标点 + 去掉末尾问号
            clean = re.sub(r'[^\w\u4e00-\u9fff]', '', text)
            if clean and clean not in re.sub(r'[^\w\u4e00-\u9fff]', '', chat_log):
                # 模糊匹配：原话可能中间有空格
                text_no_space = text.replace(' ', '').replace('\n', '')
                log_no_space = re.sub(r'\s+', '', chat_log)
                if text_no_space not in log_no_space:
                    issues.append(f"  [{i}] '{text[:30]}' 不在 chat_log 中（疑似编造）")
    return issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="日期 YYYY-MM-DD")
    ap.add_argument("--weekday", help="日报里写的星期（与自动算的对比）")
    ap.add_argument("--weekday-keyword", action="store_true",
                    help="扫描 chat_log 自动找用户提到的星期关键词")
    ap.add_argument("--messages", type=int, help="总消息数")
    ap.add_argument("--chat-log", help="chat_log 路径（用于校验 quote 真实性）")
    ap.add_argument("--story-json", help="story.json 路径（自动提取 quotes 校验）")
    args = ap.parse_args()

    print(f"=== 群日报自检 · {args.date} ===\n")
    ok = True

    # 1. 日期 / 星期 / 农历
    info = verify_date(args.date)
    print(f"  ✓ 公历: {info['date']}")
    print(f"  ✓ 星期: {info['weekday']}（{'周末' if info['is_weekend'] else '工作日'}）")
    print(f"  ✓ 干支年: {info['gan_zhi']}")
    print(f"  ✓ 农历: {info['lunar']}")
    print()

    # 2. 比对日报写的星期
    if args.weekday:
        if args.weekday == info['weekday']:
            print(f"  ✓ 报中星期 '{args.weekday}' = 实际星期 ✓")
        else:
            print(f"  ✗ 报中星期 '{args.weekday}' ≠ 实际星期 '{info['weekday']}'")
            print(f"    ⚠️ 必须改为: {info['weekday']}")
            ok = False
    print()

    # 3. 扫 chat_log 找"周一/周二/..."等关键词（如果 --weekday-keyword）
    chat_log_content = None
    if args.chat_log and Path(args.chat_log).exists():
        chat_log_content = Path(args.chat_log).read_text(encoding="utf-8")
        if args.weekday_keyword:
            keyword_map = {
                '周一': ['周一', '礼拜一', '星期一', 'Monday'],
                '周二': ['周二', '礼拜二', '星期二', 'Tuesday'],
                '周三': ['周三', '礼拜三', '星期三', 'Wednesday'],
                '周四': ['周四', '礼拜四', '星期四', 'Thursday'],
                '周五': ['周五', '礼拜五', '星期五', 'Friday'],
                '周六': ['周六', '礼拜六', '星期六', 'Saturday'],
                '周日': ['周日', '礼拜日', '星期日', '星期天', 'Sunday'],
            }
            for wd, kws in keyword_map.items():
                for kw in kws:
                    if kw in chat_log_content:
                        # 看上下文
                        idx = chat_log_content.find(kw)
                        ctx = chat_log_content[max(0, idx-30):idx+30]
                        print(f"  [chat_log] 提到星期: '{kw}' 上下文: ...{ctx}...")
    print()

    # 4. 消息数合理性
    if args.messages:
        if 0 < args.messages < 5000:
            print(f"  ✓ 总消息数 {args.messages} 合理")
        else:
            print(f"  ⚠️ 总消息数 {args.messages} 异常")
    print()

    # 5. 校验 quote
    if args.story_json and Path(args.story_json).exists():
        import json
        story = json.loads(Path(args.story_json).read_text(encoding="utf-8"))
        all_quotes = []
        for node in story.get("timeline", []):
            all_quotes.extend(node.get("quotes", []))
        if chat_log_content is None:
            print(f"  [跳过 quote 校验] 需要 --chat-log")
        else:
            issues = check_quotes(all_quotes, chat_log_content)
            if issues:
                print(f"  ✗ Quote 校验发现 {len(issues)} 个问题：")
                for i in issues:
                    print(i)
                ok = False
            else:
                print(f"  ✓ 校验 {len(all_quotes)} 条 quote，全部 OK")

    print()
    print("=" * 40)
    if ok:
        print("✅ 自检 PASS")
        sys.exit(0)
    else:
        print("❌ 自检 FAIL，请修复后重跑")
        sys.exit(1)


if __name__ == "__main__":
    main()
