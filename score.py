"""運の重なりスコア。暦・六曜・凶日・月・水星逆行の点数を足して、その日の強さを出す。

点数は管理人が決めた目安(言い伝えでの格の高さ順)。根拠のある数字ではないので、
サイトにも配点をそのまま公開する。配点を変えるときは WEIGHTS だけ直せばよい。
"""

from __future__ import annotations

from datetime import date, timedelta

import koyomi

# 要素ごとの点数(プラス=吉、マイナス=凶・注意)
WEIGHTS = {
    "天赦日": 5, "一粒万倍日": 3, "己巳の日": 3, "寅の日": 2, "巳の日": 2, "甲子の日": 2,
    "大明日": 1, "新月": 2, "満月": 1,
    "大安": 2, "友引": 1, "先勝": 0, "先負": 0, "赤口": -1, "仏滅": -2,
    "不成就日": -3, "八専": -1, "土用": -1, "三隣亡": -1, "水星逆行": -1,
}

# 吉の要素ごとの「この日にやるとよい」とされること(言い伝え)
ACTIONS = {
    "天赦日": "先延ばしにしていたことを始める（最上の吉日とされる）",
    "一粒万倍日": "財布をおろす・口座開設など「増やしたい」ことを始める",
    "己巳の日": "弁財天にお参りする（巳の日の中でも特別とされる）",
    "寅の日": "旅行の予約・財布の新調など「出して戻す」お金の使い方",
    "巳の日": "財布の中を整理して、お札の向きをそろえる",
    "甲子の日": "60日に1度の始まりの日。新しい習慣を1つ始める",
    "新月": "願いごとを紙に書く（始まりの日とされる）",
    "満月": "財布や部屋の不要な物を手放す",
    "大安": "契約・申し込み・お祝いごと",
    "大明日": "引っ越し・旅行など、外へ向かうこと",
    "友引": "お祝いごと・人に会う予定（葬事は避けるとされる）",
}

# 凶・注意の要素ごとの「控えるとよい」とされること
CAUTIONS = {
    "不成就日": "新しい契約・申し込みは別の日へ（物事が成就しにくいとされる）",
    "水星逆行": "契約・大きな買い物・送信の前に見直しを",
    "三隣亡": "建築・引っ越しの決めごとは避ける",
    "土用": "土いじり・引っ越しは控えめに",
    "八専": "大事な決めごとは慎重に",
    "仏滅": "新しいことより、片づけ・整理に向く日",
    "赤口": "お祝いごとは正午前後に",
}

LEVELS = [  # (この点以上, 星の数, ひとこと)
    (8, 5, "勝負日"),
    (5, 4, "攻めの日"),
    (2, 3, "まずまず"),
    (0, 2, "ふつう"),
    (-99, 1, "守りの日"),
]


def elements(d: date) -> list[str]:
    """その日に当たる要素(点数のあるもの)を、点数の高い順に。"""
    info = koyomi.day_info(d)
    names = [n for n in info["kichijitsu"] if n != "大安"] + [info["rokuyo"]] + info["kyojitsu"]
    if info["moon"]["event"]:
        names.append(info["moon"]["event"])
    if info["mercury_retrograde"]:
        names.append("水星逆行")
    names = [n for n in dict.fromkeys(names) if WEIGHTS.get(n, 0) != 0]
    return sorted(names, key=lambda n: -WEIGHTS[n])


def day_score(d: date) -> dict:
    names = elements(d)
    total = sum(WEIGHTS[n] for n in names)
    stars, label = next((s, lb) for th, s, lb in LEVELS if total >= th)
    plus = [n for n in names if WEIGHTS[n] > 0]
    minus = [n for n in names if WEIGHTS[n] < 0]
    return {
        "date": d, "score": total, "stars": stars, "label": label,
        "plus": plus, "minus": minus,
        "actions": [ACTIONS[n] for n in plus if n in ACTIONS][:3],
        "cautions": [CAUTIONS[n] for n in minus if n in CAUTIONS][:2],
    }


def best_days(today: date, days: int = 30, limit: int = 5) -> list[dict]:
    """今日から days 日のうち、スコアの高い日(同点なら早い日)を limit 件。"""
    rows = [day_score(today + timedelta(days=i)) for i in range(days)]
    rows = [r for r in rows if r["score"] > 0]
    return sorted(rows, key=lambda r: (-r["score"], r["date"]))[:limit]


def mercury_retro_end(today: date) -> date | None:
    """今日が水星逆行中なら、その最終日。"""
    if not koyomi.mercury_retrograde(today):
        return None
    d = today
    while koyomi.mercury_retrograde(d + timedelta(days=1)):
        d += timedelta(days=1)
    return d
