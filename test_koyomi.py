"""暦の計算を、外部の暦一覧(2026年)と照合するテスト。

参照元:
- 一粒万倍日・天赦日・寅の日・巳の日: JALの「2026年の吉日一覧」
  https://skywardplus.jal.co.jp/plus_one/calendar/ichiryumanbai_day
- 六曜(2026年10月): https://www.bestcalendar.jp/2026/10/taian
"""

from datetime import date, timedelta

import koyomi

ICHIRYU_2026 = {
    1: [1, 2, 5, 14, 17, 26, 29], 2: [8, 13, 20, 25], 3: [4, 5, 12, 17, 24, 29],
    4: [8, 11, 20, 23], 5: [2, 5, 6, 17, 18, 29, 30], 6: [12, 13, 24, 25],
    7: [6, 7, 10, 19, 22, 31], 8: [3, 13, 18, 25, 30], 9: [6, 7, 14, 19, 26],
    10: [1, 11, 14, 23, 26], 11: [4, 7, 8, 19, 20], 12: [1, 2, 15, 16, 27, 28],
}
# 8/30・9/19・11/8 はJALの一覧に無いが、All About の一覧(年64回)には載っており、
# 節月と日支の規則からも一粒万倍日になる。https://allabout.co.jp/gm/gc/516577/
TENSHA_2026 = [(3, 5), (5, 4), (5, 20), (7, 19), (10, 1), (12, 16)]
TORA_2026 = {
    1: [4, 16, 28], 2: [9, 21], 3: [5, 17, 29], 4: [10, 22], 5: [4, 16, 28], 6: [9, 21],
    7: [3, 15, 27], 8: [8, 20], 9: [1, 13, 25], 10: [7, 19, 31], 11: [12, 24], 12: [6, 18, 30],
}
MI_2026 = {
    1: [7, 19, 31], 2: [12, 24], 3: [8, 20], 4: [1, 13, 25], 5: [7, 19, 31], 6: [12, 24],
    7: [6, 18, 30], 8: [11, 23], 9: [4, 16, 28], 10: [10, 22], 11: [3, 15, 27], 12: [9, 21],
}
TSUCHINOTOMI_2026 = [(2, 24), (4, 25), (6, 24), (8, 23), (10, 22), (12, 21)]
ROKUYO_2026_10 = [
    "仏滅", "大安", "赤口", "先勝", "友引", "先負", "仏滅", "大安", "赤口", "先勝",
    "先負", "仏滅", "大安", "赤口", "先勝", "友引", "先負", "仏滅", "大安", "赤口",
    "先勝", "友引", "先負", "仏滅", "大安", "赤口", "先勝", "友引", "先負", "仏滅", "大安",
]


def _days_2026():
    d = date(2026, 1, 1)
    while d.year == 2026:
        yield d
        d += timedelta(days=1)


def _expected(table):
    return {date(2026, m, day) for m, days in table.items() for day in days}


def _actual(name):
    return {d for d in _days_2026() if name in koyomi.kichijitsu(d)}


def test_ichiryu_2026():
    assert _actual("一粒万倍日") == _expected(ICHIRYU_2026)


def test_tensha_2026():
    assert _actual("天赦日") == {date(2026, m, d) for m, d in TENSHA_2026}


def test_tora_2026():
    assert _actual("寅の日") == _expected(TORA_2026)


def test_mi_2026():
    actual = _actual("巳の日") | _actual("己巳の日")
    assert actual == _expected(MI_2026)
    assert _actual("己巳の日") == {date(2026, m, d) for m, d in TSUCHINOTOMI_2026}


def test_rokuyo_2026_10():
    actual = [koyomi.rokuyo(date(2026, 10, d)) for d in range(1, 32)]
    assert actual == ROKUYO_2026_10


def test_known_kanshi():
    assert koyomi.day_kanshi(date(2000, 1, 1)) == "戊午"
