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
import score

ROOT = Path(__file__).parent
DOCS = ROOT / "docs"
SITE_URL = "https://luck.otokuest.com"  # 正式URL(Cloudflare のカスタムドメイン)
KAIUN = ["天赦日", "一粒万倍日", "寅の日", "己巳の日", "巳の日"]  # 開運日として並べる順
LUCKY_TAGS = {"天赦日", "一粒万倍日", "大安"}


def _pick(seq: list, d: date, salt: str):
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


def _stars(n: int) -> str:
    return f'<span class="stars" aria-label="5段階中{n}">{"★" * n}<span class="off">{"★" * (5 - n)}</span></span>'


def _md(d: date) -> str:
    return f"{d.month}/{d.day}({'月火水木金土日'[d.weekday()]})"


def score_card(today: date, data: dict) -> str:
    """今日の運 重なりスコアのカード。"""
    s = score.day_score(today)
    info = koyomi.day_info(today)
    chips = "".join(f'<span class="tag lucky">{escape(n)} +{score.WEIGHTS[n]}</span>' for n in s["plus"])
    chips += "".join(f'<span class="tag minus">{escape(n)} {score.WEIGHTS[n]}</span>' for n in s["minus"])
    if not chips:
        chips = '<span class="tag">特別な暦注なし</span>'

    actions = list(s["actions"])
    if s["score"] < 0 or not actions:
        # 守りの日は、まず足元を整える(風水の言い伝え)
        actions.insert(0, _pick(data["fusui_actions"], today, "fusui")["text"])
    acts = "".join(f"<li>{escape(a)}</li>" for a in actions[:3])
    cauts = "".join(f"<li>{escape(c)}</li>" for c in s["cautions"])

    moon = info["moon"]
    sky = [f'月齢 {moon["age"]}' + (f'（{moon["event"]}）' if moon["event"] else "")]
    end = score.mercury_retro_end(today)
    if end:
        sky.append(f"水星逆行中（〜{_md(end)}）")
    if info["sekki"]:
        sky.append(f"今日から{info['sekki']}")

    best = []
    for r in score.best_days(today):
        label = "今日" if r["date"] == today else _md(r["date"])
        best.append(f'<li><span class="d">{label}</span>{_stars(r["stars"])}'
                    f'<span class="why">{escape("・".join(r["plus"][:3]))}</span></li>')
    best_html = "".join(best) or '<li class="note">30日以内にプラスの日はありません</li>'

    weights = "".join(
        f'<span class="w {"neg" if v < 0 else ""}">{escape(k)} {v:+d}</span>'
        for k, v in sorted(score.WEIGHTS.items(), key=lambda kv: -kv[1]) if v != 0)

    return f"""
    <section class="card score-card" aria-labelledby="h-score">
      <div class="card-head"><h2 id="h-score">今日の運 重なりスコア</h2><span class="badge">毎日自動更新</span></div>
      <div class="score-grid">
        <div>
          <div class="score-top">
            <div class="score-num mono">{s["score"]:+d}</div>
            <div>{_stars(s["stars"])}<div class="score-label">{escape(s["label"])}</div></div>
          </div>
          <div class="tags">{chips}</div>
          <div class="note">{escape(" ・ ".join(sky))}</div>
        </div>
        <div>
          <div class="sub-h">今日やるといいこと</div>
          <ol class="acts">{acts}</ol>
          {f'<div class="sub-h">控えたいこと</div><ul class="cauts">{cauts}</ul>' if cauts else ""}
        </div>
        <div>
          <div class="sub-h">これから30日の勝負日 TOP5</div>
          <ul class="best">{best_html}</ul>
        </div>
      </div>
      <details class="weights">
        <summary>点数のつけ方（全部公開）</summary>
        <div class="note" style="margin:6px 0">吉日・六曜・凶日・月の満ち欠け・水星逆行の点数を足しています。凶日はマイナスなので「一粒万倍日だけど不成就日」は打ち消し合います。点数は言い伝えでの格の高さから管理人が決めた目安です。</div>
        <div class="wlist">{weights}</div>
        <div class="note" style="margin-top:6px">★5＝8点以上 ／ ★4＝5〜7 ／ ★3＝2〜4 ／ ★2＝0〜1 ／ ★1＝マイナス</div>
      </details>
    </section>"""


def render(today: date, data: dict) -> str:
    info = koyomi.day_info(today)
    tags = ([_tag(info["rokuyo"])] + [_tag(n) for n in info["kichijitsu"] if n != "大安"]
            + [f'<span class="tag minus">{escape(n)}</span>' for n in info["kyojitsu"]])

    kaiun_rows = []
    for row in upcoming_kaiun(today):
        d = row["date"]
        label = "今日" if d == today else f"{d.month}/{d.day}({'月火水木金土日'[d.weekday()]})"
        kaiun_rows.append(
            f'<li><span class="d">{label}</span>{"".join(_tag(n, True) for n in row["names"])}</li>')

    odds_rows = []
    for o in data["odds"]:
        # 出典(URL)が確認できた数字だけを載せる
        if not (o.get("value") and o.get("url")):
            continue
        odds_rows.append(
            f'<div><span>{escape(o["name"])} <a class="src" href="{escape(o["url"])}" '
            f'target="_blank" rel="noopener" title="{escape(o["source"])}">出典</a></span>'
            f'<span class="v">{escape(o["value"])}</span></div>')

    log = data["observation_logs"][-1]
    pl = data.get("pachinko_logs", [])
    total = sum(p["balance"] for p in pl)
    pachi = ""
    if pl:
        cls = "loss" if total < 0 else "win"
        pachi = (
            f'<div class="log-row"><span class="k">パチンコ収支（{len(pl)}回分）</span>'
            f'<span class="n {cls}">{total:+,}円</span></div>')
    log_card = (
        f'<div class="card-head"><h2 id="h-log">運の観測ログ</h2><span class="badge">{escape(log["id"])}</span></div>'
        f'<div class="note">競馬AI（複勝）{log["trials"]}{escape(log["unit"])} ・ {escape(log["period"])}</div>'
        f'<div class="log-row"><span class="k">回収率</span><span class="n">{log["return_rate"]}%</span>'
        f'<span class="k">的中率 {log["hit_rate"]}%</span></div>'
        f'<div class="bar" role="img" aria-label="回収率{log["return_rate"]}%(100%で収支トントン)">'
        f'<span style="width:{min(log["return_rate"], 100)}%"></span></div>'
        f'{pachi}'
        f'<div class="note" style="margin-top:6px">{escape(log["lesson"])}</div>'
    )

    fusui = _pick(data["fusui_actions"], today, "fusui")
    fusui_html = (f'{escape(fusui["text"])} <a class="src" href="{escape(fusui["url"])}" '
                  f'target="_blank" rel="noopener" title="{escape(fusui["source"])}">出典</a>')
    direction = _pick(data["directions"], today, "direction")
    dnote = data.get("direction_notes", {}).get(direction, "")
    dsrc = data.get("direction_source")
    direction_html = escape(direction) + (f'（{escape(dnote)}）' if dnote else "")
    if dnote and dsrc:
        direction_html += (f' <a class="src" href="{escape(dsrc["url"])}" target="_blank" '
                           f'rel="noopener" title="{escape(dsrc["source"])}">出典</a>')

    cats = "".join(f'<span class="chip sm">{escape(c)}</span>' for c in data.get("voice_categories", []))
    cat_row = f'<div class="chips cats">{cats}</div>' if cats else ""
    form_url = data.get("form_url", "")

    if data["voices"]:
        cards = []
        for v in data["voices"]:
            chips = "".join(_tag(v[k], True) for k in ("action", "period", "cost", "result") if v.get(k))
            cards.append(f'<article class="voice"><p>{escape(v["summary"])}</p><div class="tags" style="margin:0">{chips}</div></article>')
        voices = cat_row + f'<div class="voices">{"".join(cards)}</div>'
    else:
        voices = cat_row + '<div class="empty">まだ投稿はありません。集まったら、ここに並び、「良かった体験・損した体験に多い要素」も集計します。</div>'
    if form_url:
        button = f'<a class="btn" href="{escape(form_url)}" target="_blank" rel="noopener">体験を投稿する</a>'
    else:
        button = '<span class="btn" aria-disabled="true">投稿受付 準備中</span>'

    if data["diary"]:
        entries = []
        for e in sorted(data["diary"], key=lambda x: x["date"], reverse=True)[:3]:
            if isinstance(e.get("amount"), int):
                score = f'{e["amount"]:+,}円'
            elif isinstance(e.get("score"), int):
                score = f'運 {e["score"]:+d}'
            else:
                score = ""
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
        "{{SCORE_CARD}}": score_card(today, data),
        "{{TODAY_DATE}}": f"{today:%Y/%m/%d}（{info['weekday']}）",
        "{{TODAY_TAGS}}": "".join(tags),
        "{{TODAY_KYUREKI}}": info["kyureki"],
        "{{TODAY_KANSHI}}": info["kanshi"],
        "{{MONTH_LABEL}}": f"{today.month}月〜",
        "{{KAIUN_LIST}}": "".join(kaiun_rows),
        "{{LUCKY_ITEM}}": escape(_pick(data["lucky_items"], today, "item")),
        "{{LUCKY_COLOR}}": escape(_pick(data["lucky_colors"], today, "color")),
        "{{LUCKY_DIRECTION}}": direction_html,
        "{{FUSUI}}": fusui_html,
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
    (DOCS / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    (DOCS / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{SITE_URL}/</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq></url>\n</urlset>\n",
        encoding="utf-8")
    print(f"生成しました: {today} → docs/index.html")


if __name__ == "__main__":
    main()
