"""暦の計算(六曜・日の干支・天赦日・一粒万倍日・寅の日・巳の日など)。

外部ライブラリを使わず、天文計算(Meeus『Astronomical Algorithms』の近似式)で
新月と太陽黄経を求め、日本の旧暦(JST基準)から六曜を出す。
精度は数分程度。境目が深夜0時前後に重なる日は、ごくまれに他の暦とずれる可能性がある。
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache

JST = timezone(timedelta(hours=9))
DELTA_T_DAYS = 69.0 / 86400.0  # 地球時と世界時の差(2020年代の目安 約69秒)

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
ROKUYO = ["大安", "赤口", "先勝", "友引", "先負", "仏滅"]  # (旧暦月+旧暦日) % 6 の順

# 節月(1=立春〜, 2=啓蟄〜 ... 12=小寒〜)ごとの一粒万倍日の日支
ICHIRYU = {
    1: "丑午", 2: "酉寅", 3: "子卯", 4: "卯辰", 5: "巳午", 6: "酉午",
    7: "子未", 8: "卯申", 9: "酉午", 10: "酉戌", 11: "亥子", 12: "卯子",
}
# 季節(節月で判定)ごとの天赦日の干支
TENSHA = {"春": "戊寅", "夏": "甲午", "秋": "戊申", "冬": "甲子"}


# ---------- 基本の換算 ----------

def jd_from_datetime_utc(dt: datetime) -> float:
    """UTCのdatetimeからユリウス日(UT)を返す。"""
    dt = dt.astimezone(timezone.utc)
    y, m = dt.year, dt.month
    d = dt.day + (dt.hour + (dt.minute + (dt.second + dt.microsecond / 1e6) / 60) / 60) / 24
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524.5


def jst_midnight_jd(d: date) -> float:
    """JSTのその日の0時ちょうどのユリウス日(UT)。"""
    return jd_from_datetime_utc(datetime(d.year, d.month, d.day, tzinfo=JST))


def jst_date_from_jd(jd_ut: float) -> date:
    """ユリウス日(UT)が、JSTで何日に当たるか。"""
    base = datetime(2000, 1, 1, 12, tzinfo=timezone.utc)  # JD 2451545.0
    dt = base + timedelta(days=jd_ut - 2451545.0)
    return dt.astimezone(JST).date()


def jdn(d: date) -> int:
    """その日のユリウス通日(整数)。干支の計算に使う。"""
    return d.toordinal() + 1721425


# ---------- 太陽の黄経 ----------

def sun_longitude(jd_ut: float) -> float:
    """太陽の視黄経(度、0〜360)。"""
    t = (jd_ut + DELTA_T_DAYS - 2451545.0) / 36525.0
    l0 = 280.46646 + 36000.76983 * t + 0.0003032 * t * t
    m = math.radians(357.52911 + 35999.05029 * t - 0.0001537 * t * t)
    c = ((1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(m)
         + (0.019993 - 0.000101 * t) * math.sin(2 * m)
         + 0.000289 * math.sin(3 * m))
    omega = math.radians(125.04 - 1934.136 * t)
    lam = l0 + c - 0.00569 - 0.00478 * math.sin(omega)
    return lam % 360.0


# ---------- 新月 ----------

def new_moon_jd(k: int) -> float:
    """k番目の新月のユリウス日(UT)。k=0は2000年1月6日ごろ。"""
    t = k / 1236.85
    jde = (2451550.09766 + 29.530588861 * k + 0.00015437 * t ** 2
           - 0.000000150 * t ** 3 + 0.00000000073 * t ** 4)
    e = 1 - 0.002516 * t - 0.0000074 * t ** 2
    r = math.radians
    m = r(2.5534 + 29.10535670 * k - 0.0000014 * t ** 2 - 0.00000011 * t ** 3)
    mp = r(201.5643 + 385.81693528 * k + 0.0107582 * t ** 2 + 0.00001238 * t ** 3
           - 0.000000058 * t ** 4)
    f = r(160.7108 + 390.67050284 * k - 0.0016118 * t ** 2 - 0.00000227 * t ** 3
          + 0.000000011 * t ** 4)
    om = r(124.7746 - 1.56375588 * k + 0.0020672 * t ** 2 + 0.00000215 * t ** 3)
    s = math.sin
    corr = (-0.40720 * s(mp) + 0.17241 * e * s(m) + 0.01608 * s(2 * mp)
            + 0.01039 * s(2 * f) + 0.00739 * e * s(mp - m) - 0.00514 * e * s(mp + m)
            + 0.00208 * e * e * s(2 * m) - 0.00111 * s(mp - 2 * f)
            - 0.00057 * s(mp + 2 * f) + 0.00056 * e * s(2 * mp + m)
            - 0.00042 * s(3 * mp) + 0.00042 * e * s(m + 2 * f)
            + 0.00038 * e * s(m - 2 * f) - 0.00024 * e * s(2 * mp - m)
            - 0.00017 * s(om) - 0.00007 * s(mp + 2 * m) + 0.00004 * s(2 * mp - 2 * f)
            + 0.00004 * s(3 * m) + 0.00003 * s(mp + m - 2 * f)
            + 0.00003 * s(2 * mp + 2 * f) - 0.00003 * s(mp + m + 2 * f)
            + 0.00003 * s(mp - m + 2 * f) - 0.00002 * s(mp - m - 2 * f)
            - 0.00002 * s(3 * mp + m) + 0.00002 * s(4 * mp))
    planet = [
        (0.000325, 299.77 + 0.107408 * k - 0.009173 * t ** 2),
        (0.000165, 251.88 + 0.016321 * k), (0.000164, 251.83 + 26.651886 * k),
        (0.000126, 349.42 + 36.412478 * k), (0.000110, 84.66 + 18.206239 * k),
        (0.000062, 141.74 + 53.303771 * k), (0.000060, 207.14 + 2.453732 * k),
        (0.000056, 154.84 + 7.306860 * k), (0.000047, 34.52 + 27.261239 * k),
        (0.000042, 207.19 + 0.121824 * k), (0.000040, 291.34 + 1.844379 * k),
        (0.000037, 161.72 + 24.198154 * k), (0.000035, 239.56 + 25.513099 * k),
        (0.000023, 331.55 + 3.592518 * k),
    ]
    corr += sum(c * math.sin(r(a)) for c, a in planet)
    return jde + corr - DELTA_T_DAYS


@lru_cache(maxsize=None)
def new_moon_date(k: int) -> date:
    """k番目の新月の日付(JST)。"""
    return jst_date_from_jd(new_moon_jd(k))


def _k_near(d: date) -> int:
    return math.floor((d.year + (d.timetuple().tm_yday - 1) / 365.25 - 2000) * 12.3685)


def lunation_start(d: date) -> int:
    """その日を含む旧暦の月の、最初の新月のk。"""
    k = _k_near(d) + 2
    while new_moon_date(k) > d:
        k -= 1
    return k


# ---------- 旧暦 ----------

def _chuki_month(k: int) -> int | None:
    """k番目の新月から始まる月に含まれる中気から、旧暦の月番号を返す。中気が無ければNone(閏月)。"""
    start, end = new_moon_date(k), new_moon_date(k + 1)
    d = start
    while d < end:
        before = sun_longitude(jst_midnight_jd(d))
        after = sun_longitude(jst_midnight_jd(d + timedelta(days=1)))
        if math.floor(before / 30) != math.floor(after / 30):
            sector = math.floor(after / 30) % 12  # 0=春分(0度) ... 11=雨水(330度)
            month = (sector + 2) % 12
            return 12 if month == 0 else month
        d += timedelta(days=1)
    return None


@lru_cache(maxsize=None)
def lunar_month_number(k: int) -> tuple[int, bool]:
    """(旧暦の月番号, 閏月かどうか)。"""
    month = _chuki_month(k)
    if month is not None:
        return month, False
    prev, _ = lunar_month_number(k - 1)
    return prev, True


def kyureki(d: date) -> tuple[int, int, bool]:
    """(旧暦の月, 日, 閏月か)。"""
    k = lunation_start(d)
    month, leap = lunar_month_number(k)
    day = (d - new_moon_date(k)).days + 1
    return month, day, leap


def rokuyo(d: date) -> str:
    month, day, _ = kyureki(d)
    return ROKUYO[(month + day) % 6]


# ---------- 干支・節月 ----------

def day_kanshi(d: date) -> str:
    idx = (jdn(d) + 49) % 60  # 0=甲子
    return STEMS[idx % 10] + BRANCHES[idx % 12]


def sekki_month(d: date) -> int:
    """節月(1=立春〜 ... 12=小寒〜)。節入りの日はその日から新しい月とする。"""
    lam = sun_longitude(jst_midnight_jd(d + timedelta(days=1)))
    return math.floor(((lam - 315.0) % 360.0) / 30.0) + 1


def season(d: date) -> str:
    return ["春", "夏", "秋", "冬"][(sekki_month(d) - 1) // 3]


# ---------- 吉日の判定 ----------

def kichijitsu(d: date) -> list[str]:
    """その日に当たる吉日の名前の一覧。"""
    ks = day_kanshi(d)
    branch = ks[1]
    names = []
    if ks == TENSHA[season(d)]:
        names.append("天赦日")
    if branch in ICHIRYU[sekki_month(d)]:
        names.append("一粒万倍日")
    if branch == "寅":
        names.append("寅の日")
    if ks == "己巳":
        names.append("己巳の日")
    elif branch == "巳":
        names.append("巳の日")
    if rokuyo(d) == "大安":
        names.append("大安")
    return names


def day_info(d: date) -> dict:
    month, day, leap = kyureki(d)
    return {
        "date": d.isoformat(),
        "weekday": "月火水木金土日"[d.weekday()],
        "rokuyo": rokuyo(d),
        "kanshi": day_kanshi(d),
        "kyureki": f"{'閏' if leap else ''}{month}月{day}日",
        "kichijitsu": kichijitsu(d),
    }


def month_days(year: int, month: int) -> list[dict]:
    d = date(year, month, 1)
    out = []
    while d.month == month:
        out.append(day_info(d))
        d += timedelta(days=1)
    return out


if __name__ == "__main__":
    import json
    import sys

    target = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else datetime.now(JST).date()
    print(json.dumps(day_info(target), ensure_ascii=False, indent=2))
