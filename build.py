"""サイトを生成する。docs/ に index.html・style.css・koyomi.json を書き出す。

使い方:
    python build.py              # 今日(JST)の内容で生成
    python build.py 2026-10-11   # 日付を指定して生成(確認用)
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import date, datetime, timedelta
from html import escape
from pathlib import Path

import koyomi

ROOT = Path(__file__).parent
DOCS = ROOT / "docs"
KAIUN = ["天赦日", "一粒万倍日", "寅の日", "己巳の日", "巳の日"]  # 開運日として並べる順
LUCKY_TAGS = {"天赦日", "一粒万倍日", "大安"}


def _pick(seq: list[str], d: date, salt: str) -> str:
    """日付から決まった1つを選ぶ(同じ日は何度ビルドしても同じ結果)。"""
    h = hashlib.sha256(f"{d.isoformat()}:{salt}".encode()).hexdigest()
    return seq[int(h, 16) % len(seq)]


def _tag(name: str, small: bool = False) -> str:
    cls = "tag" + (" lucky" if name in LUCKY_TAGS else "") + (" sm" if small else "")
    return f'<span class="{cls}">{escape(name)}</span>'


def upcoming_kaiun(today: date, limit: int = 6) -> list[dict]:
    """今日から先の開運日(天赦日・一粒万倍日・寅の日・巳の日)を最大limit件。"""
    out, d = [], today
    while len(out) < limit and (d - today).days < 60:
        names = [n for n in KAIUN if n in koyomi.kichijitsu(d)]
        if names:
            out.append({"date": d, "names": names})
        d += timedelta(days=1)
    return out


def render(today: date, data: dict) -> str:
    info = koyomi.day_info(today)
    tags = [_tag(info["rokuyo"])] + [_tag(n) for n in info["kichijitsu"] if n != "大安"]

    kaiun_rows = []
    for row in upcoming_kaiun(today):
        d = row["date"]
        label = "今日" if d == today else f"{d.month}/{d.day}({'月火水木金土日'[d.weekday()]})"
        kaiun_rows.append(
            f'<li><span class="d">{label}</span>{"".join(_tag(n, True) for n in row["names"])}</li>')

    odds_rows = []
    for o in data["odds"]:
        if o["value"]:
            odds_rows.append(f'<div><span>{escape(o["name"])}</span><span class="v">{escape(o["value"])}</span></div>')
        else:
            odds_rows.append(f'<div><span>{escape(o["name"])}</span><span class="v pending">出典確認中</span></div>')

    log = data["observation_logs"][-1]
    log_card = (
        f'<div class="card-head"><h2 id="h-log">運の観測ログ</h2><span class="badge">{escape(log["id"])}</span></div>'
        f'<div style="font-size:13px">{escape(log["title"])}（{log["trials"]}{escape(log["unit"])}）</div>'
        f'<div class="note">{escape(log["period"])}</div>'
        f'<div class="stat"><div><span class="k">回収率 </span><span class="n">{log["return_rate"]}%</span></div>'
        f'<div><span class="k">的中率 </span><span class="n s">{log["hit_rate"]}%</span></div></div>'
        f'<div class="bar" role="img" aria-label="回収率{log["return_rate"]}%(100%で収支トントン)">'
        f'<span style="width:{min(log["return_rate"], 100)}%"></span></div>'
        f'<div class="note" style="margin-top:6px">{escape(log["lesson"])}</div>'
    )

    if data["voices"]:
        cards = []
        for v in data["voices"]:
            chips = "".join(_tag(v[k], True) for k in ("action", "period", "cost", "result") if v.get(k))
            cards.append(f'<article class="voice"><p>{escape(v["summary"])}</p><div class="tags" style="margin:0">{chips}</div></article>')
        voices = f'<div class="voices">{"".join(cards)}</div>'
        button = '<a class="btn" href="#voices">体験談を投稿する</a>'
    else:
        voices = '<div class="empty">投稿の受付は準備中です。始まったら、ここに体験談と「良かった体験・損した体験に多い要素」が並びます。</div>'
        button = '<span class="btn" aria-disabled="true">投稿受付 準備中</span>'

    if data["diary"]:
        entries = []
        for e in sorted(data["diary"], key=lambda x: x["date"], reverse=True)[:3]:
            score = f'運 {e["score"]:+d}' if isinstance(e.get("score"), int) else ""
            entries.append(
                f'<article><div class="meta"><span>{escape(e["date"])}</span><span>{score}</span></div>'
                f'<div>{escape(e["text"])}</div>'
                + (f'<div class="lesson">学び: {escape(e["lesson"])}</div>' if e.get("lesson") else "")
                + "</article>")
        diary = f'<div class="diary">{"".join(entries)}</div>'
    else:
        diary = '<div class="empty">最初の記録を準備中。</div>'

    html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    now = datetime.now(koyomi.JST)
    repl = {
        "{{TODAY_DATE}}": f"{today:%Y/%m/%d}（{info['weekday']}）",
        "{{TODAY_TAGS}}": "".join(tags),
        "{{TODAY_KYUREKI}}": info["kyureki"],
        "{{TODAY_KANSHI}}": info["kanshi"],
        "{{MONTH_LABEL}}": f"{today.month}月〜",
        "{{KAIUN_LIST}}": "".join(kaiun_rows),
        "{{LUCKY_ITEM}}": escape(_pick(data["lucky_items"], today, "item")),
        "{{LUCKY_COLOR}}": escape(_pick(data["lucky_colors"], today, "color")),
        "{{LUCKY_DIRECTION}}": escape(_pick(data["directions"], today, "direction")),
        "{{ODDS_ROWS}}": "".join(odds_rows),
        "{{LOG_CARD}}": log_card,
        "{{VOICE_BUTTON}}": button,
        "{{VOICES}}": voices,
        "{{DIARY}}": diary,
        "{{UPDATED_AT}}": f"{now:%Y/%m/%d %H:%M}",
    }
    for k, v in repl.items():
        html = html.replace(k, v)
    assert "{{" not in html, "置き換え漏れがあります"
    return html


def main() -> None:
    today = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else datetime.now(koyomi.JST).date()
    data = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
    DOCS.mkdir(exist_ok=True)
    (DOCS / "index.html").write_text(render(today, data), encoding="utf-8")
    shutil.copy(ROOT / "templates" / "style.css", DOCS / "style.css")
    month = koyomi.month_days(today.year, today.month)
    (DOCS / "koyomi.json").write_text(json.dumps(month, ensure_ascii=False, indent=1), encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    print(f"生成しました: {today} → docs/index.html")


if __name__ == "__main__":
    main()
