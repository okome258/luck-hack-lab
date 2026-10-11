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


# ---------- 追加分(2026-10-12) ----------
# 不成就日: ゼクシィ「2026年の不成就日」 https://zexy.net/article/app002603002/
FUJOJU_2026 = {
    1: [1, 9, 17, 24], 2: [1, 9, 19, 27], 3: [7, 15, 20, 28], 4: [5, 13, 17, 25],
    5: [3, 11, 20, 28], 6: [5, 13, 19, 27], 7: [5, 13, 19, 27], 8: [4, 12, 15, 23, 31],
    9: [8, 12, 20, 28], 10: [6, 11, 19, 27], 11: [4, 12, 20, 28], 12: [6, 13, 21, 29],
}
# 三隣亡: 東急リバブル l-note https://www.livable.co.jp/l-note/?p=26914
SANRINBO_2026 = {
    1: [4, 8, 20], 2: [1, 6, 18], 3: [2, 5, 17, 29], 4: [14, 26], 5: [13, 25], 6: [9, 21],
    7: [3, 7, 19, 31], 8: [17, 29], 9: [13, 25], 10: [7, 11, 23], 11: [4, 9, 21], 12: [3, 18, 30],
}
# 大明日: bestcalendar.jp 2026年10〜12月 https://www.bestcalendar.jp/2026/10
DAIMYO_2026 = {
    10: [2, 3, 4, 9, 11, 12, 13, 14, 22, 23, 24, 25, 26, 30],
    11: [1, 4, 6, 9, 14, 17, 24, 26, 27, 28, 29],
    12: [1, 2, 3, 8, 10, 11, 12, 13, 21, 22, 23, 24, 25, 29, 31],
}
# 朔・望・二十四節気・土用の入り: 国立天文台「令和8年暦要項」
# https://eco.mtk.nao.ac.jp/koyomi/yoko/2026/rekiyou263.html / rekiyou262.html
NEW_MOON_2026 = [(1, 19), (2, 17), (3, 19), (4, 17), (5, 17), (6, 15), (7, 14), (8, 13),
                 (9, 11), (10, 11), (11, 9), (12, 9)]
FULL_MOON_2026 = [(1, 3), (2, 2), (3, 3), (4, 2), (5, 2), (5, 31), (6, 30), (7, 29), (8, 28),
                  (9, 27), (10, 26), (11, 24), (12, 24)]
SEKKI_2026 = {
    (1, 5): "小寒", (1, 20): "大寒", (2, 4): "立春", (2, 19): "雨水", (3, 5): "啓蟄",
    (3, 20): "春分", (4, 5): "清明", (4, 20): "穀雨", (5, 5): "立夏", (5, 21): "小満",
    (6, 6): "芒種", (6, 21): "夏至", (7, 7): "小暑", (7, 23): "大暑", (8, 7): "立秋",
    (8, 23): "処暑", (9, 7): "白露", (9, 23): "秋分", (10, 8): "寒露", (10, 23): "霜降",
    (11, 7): "立冬", (11, 22): "小雪", (12, 7): "大雪", (12, 22): "冬至",
}
DOYO_START_2026 = [(1, 17), (4, 17), (7, 20), (10, 20)]
# 水星逆行(日本時間): bestcalendar.jp https://bestcalendar.jp/horoscope/mercury-retrograde
MERCURY_RETRO_2026 = [((2, 26), (3, 21)), ((6, 30), (7, 24)), ((10, 24), (11, 14))]


def _on(fn):
    return {d for d in _days_2026() if fn(d)}


def test_fujoju_2026():
    assert _on(koyomi.is_fujoju) == _expected(FUJOJU_2026)


def test_sanrinbo_2026():
    assert _on(lambda d: "三隣亡" in koyomi.kyojitsu(d)) == _expected(SANRINBO_2026)


def test_daimyo_2026():
    actual = {d for d in _on(lambda d: "大明日" in koyomi.kichijitsu_extra(d)) if d.month >= 10}
    assert actual == _expected(DAIMYO_2026)


def test_moon_2026():
    assert _on(lambda d: koyomi.moon_phase(d)["event"] == "新月") == {date(2026, m, d) for m, d in NEW_MOON_2026}
    assert _on(lambda d: koyomi.moon_phase(d)["event"] == "満月") == {date(2026, m, d) for m, d in FULL_MOON_2026}


def test_sekki_2026():
    actual = {(d.month, d.day): koyomi.sekki_today(d) for d in _days_2026() if koyomi.sekki_today(d)}
    assert actual == SEKKI_2026


def test_doyo_2026():
    starts = {d for d in _days_2026() if koyomi.is_doyo(d) and not koyomi.is_doyo(d - timedelta(days=1))}
    assert starts == {date(2026, m, d) for m, d in DOYO_START_2026}


def test_mercury_retrograde_2026():
    expected = set()
    for (m1, d1), (m2, d2) in MERCURY_RETRO_2026:
        d = date(2026, m1, d1)
        while d <= date(2026, m2, d2):
            expected.add(d)
            d += timedelta(days=1)
    assert _on(koyomi.mercury_retrograde) == expected


def test_hassen():
    # 2026/10/13 は庚申(八専)、10/11 は戊午(間日)
    assert "八専" in koyomi.kyojitsu(date(2026, 10, 13))
    assert "八専" not in koyomi.kyojitsu(date(2026, 10, 11))
