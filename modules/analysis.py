"""ロト7の統計分析モジュール"""

import pandas as pd
import numpy as np
from collections import Counter
from itertools import combinations
from .data import get_main_numbers

NUMBER_MIN = 1
NUMBER_MAX = 37
ALL_NUMBERS = list(range(NUMBER_MIN, NUMBER_MAX + 1))


def get_frequency(df: pd.DataFrame) -> Counter:
    """各番号の出現回数を返す"""
    all_nums = [n for row in get_main_numbers(df) for n in row]
    counter = Counter({n: 0 for n in ALL_NUMBERS})
    counter.update(all_nums)
    return counter


def get_frequency_df(df: pd.DataFrame) -> pd.DataFrame:
    """頻度 DataFrame を返す。列: number, count, pct, color"""
    freq = get_frequency(df)
    total_draws = len(df)
    expected = total_draws * 7 / 37

    rows = []
    for n in ALL_NUMBERS:
        cnt = freq[n]
        rows.append(
            {
                "number": n,
                "count": cnt,
                "pct": round(cnt / (total_draws * 7) * 100, 1) if total_draws > 0 else 0,
                "color": _freq_color(cnt, expected),
            }
        )
    return pd.DataFrame(rows)


def _freq_color(count: int, expected: float) -> str:
    ratio = count / expected if expected > 0 else 1.0
    if ratio >= 1.3:
        return "#e74c3c"
    elif ratio >= 1.1:
        return "#e67e22"
    elif ratio <= 0.7:
        return "#3498db"
    elif ratio <= 0.9:
        return "#2ecc71"
    else:
        return "#95a5a6"


def get_hot_cold_numbers(df: pd.DataFrame, top_n: int = 7) -> tuple[list, list]:
    """ホット番号とコールド番号を返す"""
    freq = get_frequency(df)
    sorted_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    hot = sorted_freq[:top_n]
    cold = sorted_freq[-top_n:][::-1]
    return hot, cold


def get_recent_activity(df: pd.DataFrame, last_n: int = 10) -> dict[int, int]:
    """直近 last_n 回での各番号の出現回数を返す"""
    recent = df.tail(last_n)
    all_nums = [n for row in get_main_numbers(recent) for n in row]
    freq = {n: 0 for n in ALL_NUMBERS}
    for n in all_nums:
        freq[n] += 1
    return freq


def get_last_appearance(df: pd.DataFrame) -> dict[int, int]:
    """各番号が最後に出現した回からの経過回数を返す"""
    latest_round = df["round"].max()
    last_seen = {n: None for n in ALL_NUMBERS}

    for _, row in df.iterrows():
        nums = [row[f"n{i}"] for i in range(1, 8)]
        for n in nums:
            if last_seen[n] is None or row["round"] > last_seen[n]:
                last_seen[n] = row["round"]

    result = {}
    for n in ALL_NUMBERS:
        if last_seen[n] is None:
            result[n] = len(df)
        else:
            result[n] = latest_round - last_seen[n]
    return result


def get_pattern_stats(df: pd.DataFrame) -> dict:
    """各回の数字パターン統計を返す"""
    odd_even = Counter()
    high_low = Counter()
    sums = []
    consec_counts = []

    for nums in get_main_numbers(df):
        nums_sorted = sorted(nums)
        odd_count = sum(1 for n in nums_sorted if n % 2 == 1)
        odd_even[odd_count] += 1
        high_count = sum(1 for n in nums_sorted if n >= 19)
        high_low[high_count] += 1
        sums.append(sum(nums_sorted))
        consec = sum(1 for a, b in zip(nums_sorted, nums_sorted[1:]) if b - a == 1)
        consec_counts.append(consec)

    for k in range(8):
        if k not in odd_even:
            odd_even[k] = 0
        if k not in high_low:
            high_low[k] = 0

    return {
        "odd_even_distribution": dict(sorted(odd_even.items())),
        "high_low_distribution": dict(sorted(high_low.items())),
        "sum_distribution": sums,
        "consecutive_counts": consec_counts,
    }


def get_typical_pattern(df: pd.DataFrame) -> dict:
    """過去データから典型的なパターンを返す"""
    stats = get_pattern_stats(df)

    typical_odd = max(stats["odd_even_distribution"], key=stats["odd_even_distribution"].get)
    typical_high = max(stats["high_low_distribution"], key=stats["high_low_distribution"].get)
    sums = stats["sum_distribution"]
    typical_sum_center = int(np.median(sums))
    typical_sum_std = int(np.std(sums))

    consec = stats["consecutive_counts"]
    typical_consec = max(set(consec), key=consec.count) if consec else 1

    return {
        "typical_odd_count": typical_odd,
        "typical_even_count": 7 - typical_odd,
        "typical_high_count": typical_high,
        "typical_low_count": 7 - typical_high,
        "sum_median": typical_sum_center,
        "sum_std": typical_sum_std,
        "sum_lo": typical_sum_center - typical_sum_std,
        "sum_hi": typical_sum_center + typical_sum_std,
        "typical_consec": typical_consec,
    }


# ────────────────────────────────────────────
#  共起分析（ペア頻度）
# ────────────────────────────────────────────
def get_streak_stats(df: pd.DataFrame) -> dict[int, dict]:
    """
    各番号の連続出現ストリーク情報を返す。

    Returns: {
        number: {
            "current_streak": int,   # 最新回から何連続で出ているか (0=前回出ていない)
            "max_streak": int,       # 過去最大の連続出現回数
            "all_streaks": list,     # 全ストリークのリスト (長さ)
        }
    }
    """
    all_draws = get_main_numbers(df)
    results = {}

    for n in ALL_NUMBERS:
        # 各回で出たか (True/False) のリスト（古い順）
        appeared = [n in [int(x) for x in draw] for draw in all_draws]

        streaks = []
        current = 0
        for a in appeared:
            if a:
                current += 1
            else:
                if current > 0:
                    streaks.append(current)
                current = 0
        # 最後のストリーク（進行中）
        if current > 0:
            streaks.append(current)

        # 現在のストリーク = 最新回から遡って何連続か
        current_streak = 0
        for a in reversed(appeared):
            if a:
                current_streak += 1
            else:
                break

        results[n] = {
            "current_streak": current_streak,
            "max_streak": max(streaks) if streaks else 0,
            "all_streaks": streaks,
        }

    return results


def get_recent_draws_text(df: pd.DataFrame, last_n: int = 20) -> str:
    """直近 last_n 回の当選番号をテキストで返す"""
    recent = df.tail(last_n)
    lines = []
    for _, row in recent.iterrows():
        r = int(row["round"])
        nums = sorted(int(row[f"n{i}"]) for i in range(1, 8))
        lines.append(f"第{r}回: {', '.join(f'{n:02d}' for n in nums)}")
    return "\n".join(lines)


def get_cooccurrence(df: pd.DataFrame) -> dict[tuple[int, int], int]:
    """
    全2番号ペアの共起回数を返す。
    同じ回に一緒に出現した回数をカウント。
    """
    pair_count: Counter = Counter()
    for nums in get_main_numbers(df):
        nums_sorted = sorted(int(n) for n in nums)
        for pair in combinations(nums_sorted, 2):
            pair_count[pair] += 1
    return dict(pair_count)


def get_cooccurrence_score(df: pd.DataFrame) -> dict[int, float]:
    """
    各番号の「共起力」スコアを返す。
    よく一緒に出る相手が多い番号ほどスコアが高い。
    """
    pair_count = get_cooccurrence(df)
    total_draws = len(df)
    expected_pair = total_draws * (7 * 6) / (37 * 36)  # 任意ペアの期待共起回数

    # 各番号について、期待値を超えるペアの超過分を合計
    co_score = {n: 0.0 for n in ALL_NUMBERS}
    for (a, b), cnt in pair_count.items():
        excess = max(0, cnt - expected_pair)
        co_score[a] += excess
        co_score[b] += excess

    max_co = max(co_score.values()) or 1
    return {n: co_score[n] / max_co for n in ALL_NUMBERS}


def get_top_pairs(df: pd.DataFrame, top_n: int = 15) -> list[tuple[int, int, int]]:
    """共起回数上位のペアを返す: [(num_a, num_b, count), ...]"""
    pair_count = get_cooccurrence(df)
    sorted_pairs = sorted(pair_count.items(), key=lambda x: x[1], reverse=True)
    return [(a, b, c) for (a, b), c in sorted_pairs[:top_n]]


# ────────────────────────────────────────────
#  トレンド分析（直近の傾向変化）
# ────────────────────────────────────────────
def get_trend_score(df: pd.DataFrame) -> dict[int, float]:
    """
    各番号のトレンドスコアを返す。
    直近のウィンドウと少し前のウィンドウで出現率を比較し、
    上昇傾向の番号に高いスコアを付ける。

    Returns: {number: trend_score} (正=上昇傾向, 負=下降傾向, 0付近=変化なし)
             正規化して 0-1 の範囲に収める
    """
    total = len(df)
    if total < 20:
        return {n: 0.5 for n in ALL_NUMBERS}

    window = max(10, total // 10)

    # 直近ウィンドウ
    recent_df = df.tail(window)
    recent_freq = get_frequency(recent_df)

    # その前のウィンドウ
    prev_df = df.iloc[-(window * 2):-window] if total >= window * 2 else df.head(window)
    prev_freq = get_frequency(prev_df)

    recent_draws = len(recent_df)
    prev_draws = len(prev_df)

    raw_trend = {}
    for n in ALL_NUMBERS:
        recent_rate = recent_freq[n] / recent_draws if recent_draws > 0 else 0
        prev_rate = prev_freq[n] / prev_draws if prev_draws > 0 else 0
        raw_trend[n] = recent_rate - prev_rate

    # 0-1 に正規化
    min_t = min(raw_trend.values())
    max_t = max(raw_trend.values())
    rng = max_t - min_t if max_t != min_t else 1

    return {n: (raw_trend[n] - min_t) / rng for n in ALL_NUMBERS}


def get_trending_numbers(df: pd.DataFrame, top_n: int = 7) -> list[tuple[int, float]]:
    """上昇トレンド上位の番号を返す: [(number, raw_change), ...]"""
    total = len(df)
    window = max(10, total // 10)
    recent_df = df.tail(window)
    recent_freq = get_frequency(recent_df)
    prev_df = df.iloc[-(window * 2):-window] if total >= window * 2 else df.head(window)
    prev_freq = get_frequency(prev_df)
    recent_draws = len(recent_df)
    prev_draws = len(prev_df)

    changes = []
    for n in ALL_NUMBERS:
        r = recent_freq[n] / recent_draws if recent_draws > 0 else 0
        p = prev_freq[n] / prev_draws if prev_draws > 0 else 0
        changes.append((n, round(r - p, 4)))

    changes.sort(key=lambda x: x[1], reverse=True)
    return changes[:top_n]


# ────────────────────────────────────────────
#  連続出現分析（前回→今回の引き継ぎ確率）
# ────────────────────────────────────────────
def get_repeat_stats(df: pd.DataFrame) -> dict:
    """
    前回の当選番号が次の回でも出る「連続出現」の統計を返す。

    Returns: {
        "avg_repeats": float,         # 平均引き継ぎ個数
        "repeat_distribution": dict,  # {引き継ぎ個数: 回数}
        "per_number_repeat_rate": dict[int, float],  # 各番号の連続出現率 (0-1)
    }
    """
    all_draws = get_main_numbers(df)
    if len(all_draws) < 2:
        return {
            "avg_repeats": 0,
            "repeat_distribution": {},
            "per_number_repeat_rate": {n: 0 for n in ALL_NUMBERS},
        }

    repeat_counts = []
    # 各番号が「前回出て→今回も出た」回数と「前回出た」回数
    num_appeared = Counter()
    num_repeated = Counter()

    for i in range(1, len(all_draws)):
        prev = set(int(n) for n in all_draws[i - 1])
        curr = set(int(n) for n in all_draws[i])
        repeats = prev & curr
        repeat_counts.append(len(repeats))
        for n in prev:
            num_appeared[n] += 1
            if n in repeats:
                num_repeated[n] += 1

    dist = Counter(repeat_counts)
    for k in range(8):
        if k not in dist:
            dist[k] = 0

    per_number = {}
    for n in ALL_NUMBERS:
        if num_appeared[n] > 0:
            per_number[n] = num_repeated[n] / num_appeared[n]
        else:
            per_number[n] = 0.0

    return {
        "avg_repeats": sum(repeat_counts) / len(repeat_counts),
        "repeat_distribution": dict(sorted(dist.items())),
        "per_number_repeat_rate": per_number,
    }


def get_repeat_score(df: pd.DataFrame) -> dict[int, float]:
    """
    前回の当選番号に対する連続出現スコアを返す。
    前回出た番号で、かつ過去の連続出現率が高い番号ほど高スコア。
    前回出ていない番号は 0。
    """
    stats = get_repeat_stats(df)
    per_number = stats["per_number_repeat_rate"]

    # 最新回の番号
    last_draw = set(int(n) for n in get_main_numbers(df)[-1])

    raw = {}
    for n in ALL_NUMBERS:
        if n in last_draw:
            raw[n] = per_number[n]
        else:
            raw[n] = 0.0

    max_r = max(raw.values()) or 1
    return {n: raw[n] / max_r for n in ALL_NUMBERS}


# ────────────────────────────────────────────
#  連続出現ストリークスコア
# ────────────────────────────────────────────
def get_streak_score(df: pd.DataFrame) -> dict[int, float]:
    """
    各番号のストリークスコアを返す（0-1）。

    勢いカーブ: 1-3連続で上昇、3連続がピーク、4以上は減衰
      0連続 → 0.0
      1連続 → 0.5
      2連続 → 0.85
      3連続 → 1.0 (ピーク)
      4連続 → 0.7
      5連続 → 0.4
      6+連続 → 0.2

    体質スコア: 過去最大ストリークが長いほど高いが、3で頭打ち
    """
    streaks = get_streak_stats(df)

    # 勢いカーブ（連続数 → スコア）
    _momentum_curve = {0: 0.0, 1: 0.5, 2: 0.85, 3: 1.0, 4: 0.7, 5: 0.4}

    def _momentum(current: int) -> float:
        if current in _momentum_curve:
            return _momentum_curve[current]
        return 0.2  # 6連続以上

    def _tendency(max_streak: int) -> float:
        return min(max_streak / 3.0, 1.0)  # 3で頭打ち

    scores = {}
    for n in ALL_NUMBERS:
        m = _momentum(streaks[n]["current_streak"])
        t = _tendency(streaks[n]["max_streak"])
        scores[n] = m * 0.6 + t * 0.4

    return scores


# ────────────────────────────────────────────
#  パターン適合フィルタ
# ────────────────────────────────────────────
def check_pattern_fit(combo: list[int], pattern: dict) -> dict:
    """
    組み合わせが典型パターンにどれだけ適合するかを判定する。

    Returns: {
        "odd_ok": bool,
        "high_ok": bool,
        "sum_ok": bool,
        "consec_ok": bool,
        "fit_count": int,  # 適合した条件の数 (0-4)
    }
    """
    nums = sorted(combo)
    odd_count = sum(1 for n in nums if n % 2 == 1)
    high_count = sum(1 for n in nums if n >= 19)
    total = sum(nums)
    consec = sum(1 for a, b in zip(nums, nums[1:]) if b - a == 1)

    odd_ok = abs(odd_count - pattern["typical_odd_count"]) <= 1
    high_ok = abs(high_count - pattern["typical_high_count"]) <= 1
    sum_ok = pattern["sum_lo"] <= total <= pattern["sum_hi"]
    consec_ok = consec <= pattern.get("typical_consec", 2) + 1

    return {
        "odd_ok": odd_ok,
        "high_ok": high_ok,
        "sum_ok": sum_ok,
        "consec_ok": consec_ok,
        "fit_count": sum([odd_ok, high_ok, sum_ok, consec_ok]),
    }


# ────────────────────────────────────────────
#  出現間隔の規則性（周期スコア）
# ────────────────────────────────────────────
def get_interval_score(df: pd.DataFrame) -> dict[int, float]:
    """
    各番号の出現間隔の規則性スコアを返す（0-1）。

    平均出現間隔を計算し、現在の未出現回数がその間隔に
    近いほど「そろそろ出る周期」として高スコア。
    """
    all_draws = get_main_numbers(df)
    last_app = get_last_appearance(df)

    scores = {}
    for n in ALL_NUMBERS:
        # 各出現間のインターバルを計算
        appearances = []
        for i, draw in enumerate(all_draws):
            if n in [int(x) for x in draw]:
                appearances.append(i)

        if len(appearances) < 2:
            scores[n] = 0.5
            continue

        # インターバル（出現間の回数差）のリスト
        intervals = [appearances[i+1] - appearances[i] for i in range(len(appearances)-1)]
        avg_interval = sum(intervals) / len(intervals)

        # 現在の未出現回数
        current_gap = last_app[n]

        # 周期への近さ: 平均間隔に近いほど1.0、離れるほど下がる
        if avg_interval > 0:
            # 比率: current_gap / avg_interval が 1.0 に近いほど高スコア
            ratio = current_gap / avg_interval
            if ratio <= 1.0:
                # まだ周期に達していない → 近づくほど上昇
                cycle_score = ratio
            else:
                # 周期を過ぎている → 過ぎるほどさらに高スコア（出遅れ）
                # ただし2倍を超えたら頭打ち
                cycle_score = min(ratio, 2.0) / 2.0 * 1.0
                cycle_score = max(cycle_score, 0.5)
        else:
            cycle_score = 0.5

        scores[n] = min(cycle_score, 1.0)

    return scores


def get_interval_stats(df: pd.DataFrame) -> dict[int, dict]:
    """各番号の出現間隔統計を返す（表示用）"""
    all_draws = get_main_numbers(df)
    last_app = get_last_appearance(df)

    results = {}
    for n in ALL_NUMBERS:
        appearances = [i for i, draw in enumerate(all_draws) if n in [int(x) for x in draw]]

        if len(appearances) < 2:
            results[n] = {"avg_interval": 0, "current_gap": last_app[n], "cycle_ratio": 0}
            continue

        intervals = [appearances[i+1] - appearances[i] for i in range(len(appearances)-1)]
        avg = sum(intervals) / len(intervals)
        gap = last_app[n]
        ratio = gap / avg if avg > 0 else 0

        results[n] = {
            "avg_interval": round(avg, 1),
            "current_gap": gap,
            "cycle_ratio": round(ratio, 2),
        }

    return results


# ────────────────────────────────────────────
#  隣接数字効果
# ────────────────────────────────────────────
def get_neighbor_score(df: pd.DataFrame) -> dict[int, float]:
    """
    前回の当選番号に隣接する番号（±1, ±2）にボーナスを与える。
    ±1 は高め、±2 はやや低めのスコア。
    前回の番号自体には加点しない（連続出現は別要因で扱う）。
    """
    last_draw = set(int(n) for n in get_main_numbers(df)[-1])

    raw = {n: 0.0 for n in ALL_NUMBERS}
    for num in last_draw:
        for delta, weight in [(-1, 1.0), (1, 1.0), (-2, 0.5), (2, 0.5)]:
            neighbor = num + delta
            if neighbor in raw and neighbor not in last_draw:
                raw[neighbor] += weight

    max_r = max(raw.values()) or 1
    return {n: raw[n] / max_r for n in ALL_NUMBERS}


def get_neighbor_numbers(df: pd.DataFrame) -> list[tuple[int, float]]:
    """隣接効果の高い番号を表示用に返す"""
    scores = get_neighbor_score(df)
    result = [(n, s) for n, s in scores.items() if s > 0]
    result.sort(key=lambda x: x[1], reverse=True)
    return result


# ────────────────────────────────────────────
#  強化版 総合スコア
# ────────────────────────────────────────────
def get_number_score(df: pd.DataFrame) -> dict[int, float]:
    """
    各番号の総合スコアを計算して返す（強化版）。

    スコア要因と重み（9要因）:
    - 全体頻度               14%
    - 直近の活性度            10%
    - 長期未出現ボーナス        8%
    - 共起力                 13%
    - トレンド（上昇傾向）     15%
    - 連続出現（前回→次回）    11%
    - ストリーク（連続の勢い） 10%
    - 出現間隔の周期性         10%  ← NEW
    - 隣接数字効果             9%  ← NEW
    """
    total = len(df)
    freq = get_frequency(df)
    recent = get_recent_activity(df, last_n=max(10, total // 10))
    last_app = get_last_appearance(df)
    co_score = get_cooccurrence_score(df)
    trend = get_trend_score(df)
    repeat = get_repeat_score(df)
    streak = get_streak_score(df)
    streaks_raw = get_streak_stats(df)
    interval = get_interval_score(df)
    neighbor = get_neighbor_score(df)

    max_freq = max(freq.values()) or 1
    max_recent = max(recent.values()) or 1
    max_gap = max(last_app.values()) or 1

    scores = {}
    for n in ALL_NUMBERS:
        freq_s = freq[n] / max_freq
        recent_s = recent[n] / max_recent
        gap_s = last_app[n] / max_gap
        co_s = co_score[n]
        trend_s = trend[n]
        repeat_s = repeat[n]
        streak_s = streak[n]
        interval_s = interval[n]
        neighbor_s = neighbor[n]

        base = (
            freq_s * 0.14
            + recent_s * 0.10
            + gap_s * 0.08
            + co_s * 0.13
            + trend_s * 0.15
            + repeat_s * 0.11
            + streak_s * 0.10
            + interval_s * 0.10
            + neighbor_s * 0.09
        )

        # 出すぎペナルティ: 4連続以上は総合スコアを割引
        cs = streaks_raw[n]["current_streak"]
        if cs >= 6:
            base *= 0.50
        elif cs >= 5:
            base *= 0.60
        elif cs >= 4:
            base *= 0.75

        scores[n] = base

    return scores
