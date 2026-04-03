"""ロト7の統計分析モジュール"""

import pandas as pd
import numpy as np
import json as _json
from pathlib import Path as _Path
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
#  条件付き確率モデル（ベイズ的遷移確率）
# ────────────────────────────────────────────
def get_conditional_score(df: pd.DataFrame) -> dict[int, float]:
    """
    前回の当選番号7つそれぞれに対して「Aが出た次にBが出る確率」を
    ベイズ的に計算し、全7番号からの遷移確率を合成する。
    """
    all_draws = get_main_numbers(df)
    if len(all_draws) < 10:
        return {n: 0.5 for n in ALL_NUMBERS}

    # 遷移カウント: transition[a][b] = aが出た次の回にbが出た回数
    transition = {a: Counter() for a in ALL_NUMBERS}
    appear_count = Counter()

    for i in range(len(all_draws) - 1):
        curr = set(int(x) for x in all_draws[i])
        nxt = set(int(x) for x in all_draws[i + 1])
        for a in curr:
            appear_count[a] += 1
            for b in nxt:
                transition[a][b] += 1

    # 最新回の番号から各番号への遷移確率を合成
    last_draw = [int(x) for x in all_draws[-1]]
    raw = {n: 0.0 for n in ALL_NUMBERS}

    for a in last_draw:
        if appear_count[a] == 0:
            continue
        for n in ALL_NUMBERS:
            raw[n] += transition[a][n] / appear_count[a]

    # 正規化 0-1
    max_r = max(raw.values()) or 1
    return {n: raw[n] / max_r for n in ALL_NUMBERS}


# ────────────────────────────────────────────
#  時系列パターン認識（類似パターン検索）
# ────────────────────────────────────────────
def get_pattern_match_score(df: pd.DataFrame, window: int = 5) -> dict[int, float]:
    """
    直近 window 回の出目パターンに最も類似した過去パターンを探し、
    その次に出た番号にスコアを付ける。
    """
    all_draws = get_main_numbers(df)
    if len(all_draws) < window + 10:
        return {n: 0.5 for n in ALL_NUMBERS}

    # 全回の出目セットを事前計算
    draw_sets = [frozenset(int(x) for x in d) for d in all_draws]
    recent_pattern = draw_sets[-window:]

    scores_accum = {n: 0.0 for n in ALL_NUMBERS}
    total_weight = 0.0

    # 直近200回分だけ検索（全履歴は重すぎる）
    search_end = max(0, len(draw_sets) - window - 1)
    search_start = max(0, search_end - 200)

    for start in range(search_start, search_end):
        # 類似度: 各回のJaccard類似度の平均
        sim_sum = 0.0
        for i in range(window):
            rp = recent_pattern[i]
            pp = draw_sets[start + i]
            inter = len(rp & pp)
            union = len(rp | pp)
            sim_sum += inter / union if union > 0 else 0
        similarity = sim_sum / window

        if similarity < 0.15:
            continue

        next_draw = draw_sets[start + window]
        weight = similarity ** 2
        for n in next_draw:
            scores_accum[n] += weight
        total_weight += weight

    if total_weight == 0:
        return {n: 0.5 for n in ALL_NUMBERS}

    max_s = max(scores_accum.values()) or 1
    return {n: scores_accum[n] / max_s for n in ALL_NUMBERS}


# ────────────────────────────────────────────
#  アンサンブルスコア（複数期間の合議制）
# ────────────────────────────────────────────
def get_ensemble_score(df: pd.DataFrame) -> dict[int, float]:
    """
    異なる分析期間（直近50回 / 直近150回 / 全体）で別々にスコアを出し、
    複数期間で上位に入った番号を優先する合議制スコア。
    """
    total = len(df)
    periods = []
    if total >= 50:
        periods.append(df.tail(50))
    if total >= 150:
        periods.append(df.tail(150))
    periods.append(df)  # 全体

    if len(periods) < 2:
        return {n: 0.5 for n in ALL_NUMBERS}

    # 各期間でのランキングを取得
    rankings = []
    for period_df in periods:
        freq = get_frequency(period_df)
        recent = get_recent_activity(period_df, last_n=max(5, len(period_df) // 10))
        max_f = max(freq.values()) or 1
        max_r = max(recent.values()) or 1
        period_score = {}
        for n in ALL_NUMBERS:
            period_score[n] = (freq[n] / max_f) * 0.6 + (recent[n] / max_r) * 0.4
        ranked = sorted(ALL_NUMBERS, key=lambda x: period_score[x], reverse=True)
        rankings.append({n: rank for rank, n in enumerate(ranked, 1)})

    # 合議: 全期間での平均ランクが低いほど高スコア
    avg_rank = {}
    for n in ALL_NUMBERS:
        avg_rank[n] = sum(r[n] for r in rankings) / len(rankings)

    # 反転して正規化（ランク1=最高スコア）
    max_rank = max(avg_rank.values())
    min_rank = min(avg_rank.values())
    rng = max_rank - min_rank if max_rank != min_rank else 1
    return {n: (max_rank - avg_rank[n]) / rng for n in ALL_NUMBERS}


# ────────────────────────────────────────────
#  重みの自動最適化
# ────────────────────────────────────────────
_OPTIMIZED_WEIGHTS_FILE = _Path(__file__).parent.parent / ".optimized_weights.json"

DEFAULT_WEIGHTS = [0.12, 0.08, 0.06, 0.10, 0.12, 0.09, 0.08, 0.08, 0.07, 0.06, 0.07, 0.07]
FACTOR_NAMES = [
    "freq", "recent", "gap", "cooccurrence", "trend", "repeat",
    "streak", "interval", "neighbor", "conditional", "pattern_match", "ensemble",
]


def optimize_weights(df: pd.DataFrame, test_rounds: int = 30) -> list[float]:
    """
    高速版: 要因を事前計算してキャッシュし、重みの組み合わせだけを高速に評価。
    """
    total = len(df)
    if total < test_rounds + 20:
        return DEFAULT_WEIGHTS

    # ── 各テスト回の要因を事前計算（最大のボトルネックを解消）──
    test_start = max(0, total - test_rounds)
    precomputed = []  # [(actual_set, factors_matrix), ...]

    for idx in range(test_start, total):
        train_df = df.iloc[:idx]
        if len(train_df) < 10:
            continue
        actual_row = df.iloc[idx]
        actual = set(int(actual_row[f"n{i}"]) for i in range(1, 8))
        factors = _get_all_factors(train_df)
        # 番号 × 要因の行列に変換 (37 x 12)
        matrix = {n: [factors[i].get(n, 0) for i in range(len(FACTOR_NAMES))] for n in ALL_NUMBERS}
        precomputed.append((actual, matrix))

    if not precomputed:
        return DEFAULT_WEIGHTS

    def _fast_eval(weights: list[float]) -> float:
        """事前計算済み要因で高速評価"""
        hits = 0
        for actual, matrix in precomputed:
            scores = {n: sum(matrix[n][i] * weights[i] for i in range(len(weights))) for n in ALL_NUMBERS}
            top15 = set(sorted(scores, key=scores.get, reverse=True)[:15])
            hits += len(top15 & actual)
        return hits / len(precomputed)

    best_weights = DEFAULT_WEIGHTS[:]
    best_score = _fast_eval(best_weights)

    # 座標降下法（事前計算済みなので高速）
    for iteration in range(3):
        improved = False
        for i in range(len(best_weights)):
            for delta in [0.04, -0.04, 0.08, -0.08]:
                trial = best_weights[:]
                trial[i] = max(0.01, trial[i] + delta)
                s = sum(trial)
                trial = [w / s for w in trial]

                score = _fast_eval(trial)
                if score > best_score:
                    best_score = score
                    best_weights = trial
                    improved = True
        if not improved:
            break

    # 保存
    try:
        _OPTIMIZED_WEIGHTS_FILE.write_text(
            _json.dumps({
                "weights": best_weights,
                "score": round(best_score, 4),
                "factors": FACTOR_NAMES,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass

    return best_weights


def _calc_score_with_weights(df: pd.DataFrame, weights: list[float]) -> dict[int, float]:
    """指定した重みで12要因スコアを計算"""
    factors = _get_all_factors(df)
    scores = {}
    for n in ALL_NUMBERS:
        s = sum(factors[i].get(n, 0) * weights[i] for i in range(len(weights)))
        scores[n] = s
    return scores


def _get_all_factors(df: pd.DataFrame) -> list[dict[int, float]]:
    """全12要因の正規化スコアをリストで返す"""
    total = len(df)
    freq = get_frequency(df)
    recent = get_recent_activity(df, last_n=max(10, total // 10))
    last_app = get_last_appearance(df)

    max_freq = max(freq.values()) or 1
    max_recent = max(recent.values()) or 1
    max_gap = max(last_app.values()) or 1

    f_freq = {n: freq[n] / max_freq for n in ALL_NUMBERS}
    f_recent = {n: recent[n] / max_recent for n in ALL_NUMBERS}
    f_gap = {n: last_app[n] / max_gap for n in ALL_NUMBERS}
    f_co = get_cooccurrence_score(df)
    f_trend = get_trend_score(df)
    f_repeat = get_repeat_score(df)
    f_streak = get_streak_score(df)
    f_interval = get_interval_score(df)
    f_neighbor = get_neighbor_score(df)
    f_conditional = get_conditional_score(df)
    f_pattern = get_pattern_match_score(df)
    f_ensemble = get_ensemble_score(df)

    return [
        f_freq, f_recent, f_gap, f_co, f_trend, f_repeat,
        f_streak, f_interval, f_neighbor, f_conditional, f_pattern, f_ensemble,
    ]


def load_optimized_weights() -> list[float]:
    """保存された最適化重みを読み込む"""
    try:
        if _OPTIMIZED_WEIGHTS_FILE.exists():
            data = _json.loads(_OPTIMIZED_WEIGHTS_FILE.read_text(encoding="utf-8"))
            return data.get("weights", DEFAULT_WEIGHTS)
    except Exception:
        pass
    return DEFAULT_WEIGHTS


# ────────────────────────────────────────────
#  強化版 総合スコア（12要因 + 自動最適化重み）
# ────────────────────────────────────────────
def get_number_score(df: pd.DataFrame) -> dict[int, float]:
    """
    各番号の総合スコアを計算して返す（12要因版）。

    要因:
    1. 全体頻度           2. 直近の活性度
    3. 長期未出現          4. 共起力
    5. トレンド           6. 連続出現
    7. ストリーク          8. 出現間隔の周期性
    9. 隣接数字効果        10. 条件付き確率（ベイズ）
    11. パターン認識        12. アンサンブル（合議制）

    重みは自動最適化されたものを使用（なければデフォルト）。
    """
    weights = load_optimized_weights()
    factors = _get_all_factors(df)
    streaks_raw = get_streak_stats(df)

    scores = {}
    for n in ALL_NUMBERS:
        base = sum(factors[i].get(n, 0) * weights[i] for i in range(len(weights)))

        # 出すぎペナルティ
        cs = streaks_raw[n]["current_streak"]
        if cs >= 6:
            base *= 0.50
        elif cs >= 5:
            base *= 0.60
        elif cs >= 4:
            base *= 0.75

        scores[n] = base

    # フィードバック重みがあれば適用
    fb_weights = load_feedback_weights()
    if fb_weights:
        for n in ALL_NUMBERS:
            adj = fb_weights.get(str(n), 0.0)
            scores[n] *= (1.0 + adj)

    return scores


# ────────────────────────────────────────────
#  予測フィードバック機能
# ────────────────────────────────────────────
_FEEDBACK_DIR = _Path(__file__).parent.parent
_PREDICTION_FILE = _FEEDBACK_DIR / ".prediction_history.json"
_FEEDBACK_WEIGHTS_FILE = _FEEDBACK_DIR / ".feedback_weights.json"

DEFAULT_FACTOR_WEIGHTS = {
    "freq": 0.14, "recent": 0.10, "gap": 0.08,
    "cooccurrence": 0.13, "trend": 0.15, "repeat": 0.11,
    "streak": 0.10, "interval": 0.10, "neighbor": 0.09,
}


def save_predictions(round_no: int, combos: list[list[int]], scores: dict):
    """予測結果をファイルに保存する（次回の振り返り用）"""
    try:
        history = _load_prediction_history()
        # 各要因の上位番号も保存
        entry = {
            "round": round_no,
            "combos": combos[:50],  # 最大50組保存
            "top_numbers": sorted(scores, key=scores.get, reverse=True)[:15],
            "scores": {str(n): round(s, 4) for n, s in scores.items()},
        }
        # 同じラウンドは上書き
        history = [h for h in history if h.get("round") != round_no]
        history.append(entry)
        # 直近10回分だけ保持
        history = sorted(history, key=lambda x: x["round"])[-10:]
        _PREDICTION_FILE.write_text(
            _json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass


def _load_prediction_history() -> list:
    try:
        if _PREDICTION_FILE.exists():
            return _json.loads(_PREDICTION_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return []


def analyze_prediction_accuracy(df: pd.DataFrame) -> dict | None:
    """
    過去の予測と実際の結果を比較分析する。

    Returns: {
        "rounds": [
            {
                "round": int,
                "predicted_top15": [int, ...],
                "actual": [int, ...],
                "hits_in_top15": int,
                "best_combo_hits": int,
                "best_combo": [int, ...],
            }, ...
        ],
        "avg_hits_top15": float,
        "avg_best_combo_hits": float,
        "factor_accuracy": {factor_name: accuracy, ...},
        "number_over_predicted": [(num, times_predicted, times_appeared)],
        "number_under_predicted": [(num, times_not_predicted, times_appeared)],
    }
    """
    history = _load_prediction_history()
    if not history:
        return None

    all_draws = get_main_numbers(df)
    round_to_draw = {}
    for _, row in df.iterrows():
        r = int(row["round"])
        nums = sorted(int(row[f"n{i}"]) for i in range(1, 8))
        round_to_draw[r] = nums

    results = []
    over_pred = Counter()   # 予測したが出なかった回数
    under_pred = Counter()  # 予測しなかったが出た回数
    pred_count = Counter()  # 予測された回数
    appeared_count = Counter()  # 実際に出た回数

    for entry in history:
        pred_round = entry["round"]
        # この予測は「pred_round 回の結果」を予測したもの
        actual = round_to_draw.get(pred_round)
        if actual is None:
            continue  # まだ結果が出ていない

        actual_set = set(actual)
        top15 = entry.get("top_numbers", [])[:15]
        combos = entry.get("combos", [])

        hits_top15 = len(set(top15) & actual_set)

        # 最も的中が多かった組を特定
        best_hits = 0
        best_combo = []
        for combo in combos:
            h = len(set(combo) & actual_set)
            if h > best_hits:
                best_hits = h
                best_combo = combo

        results.append({
            "round": pred_round,
            "predicted_top15": top15,
            "actual": actual,
            "hits_in_top15": hits_top15,
            "best_combo_hits": best_hits,
            "best_combo": best_combo,
        })

        # 過大/過少予測の集計
        for n in top15:
            pred_count[n] += 1
            if n not in actual_set:
                over_pred[n] += 1
        for n in actual:
            appeared_count[n] += 1
            if n not in top15:
                under_pred[n] += 1

    if not results:
        return None

    avg_top15 = sum(r["hits_in_top15"] for r in results) / len(results)
    avg_best = sum(r["best_combo_hits"] for r in results) / len(results)

    # 過大予測ワースト
    over_list = sorted(
        [(n, over_pred[n], pred_count[n]) for n in over_pred if over_pred[n] > 0],
        key=lambda x: x[1], reverse=True
    )[:10]

    # 過少予測ワースト
    under_list = sorted(
        [(n, under_pred[n], appeared_count[n]) for n in under_pred if under_pred[n] > 0],
        key=lambda x: x[1], reverse=True
    )[:10]

    return {
        "rounds": results,
        "avg_hits_top15": round(avg_top15, 2),
        "avg_best_combo_hits": round(avg_best, 2),
        "number_over_predicted": over_list,
        "number_under_predicted": under_list,
    }


def update_feedback_weights(df: pd.DataFrame):
    """
    予測精度分析に基づいてフィードバック重みを更新する。

    過大予測された番号 → 次回スコアを微減
    過小予測された番号 → 次回スコアを微増
    """
    analysis = analyze_prediction_accuracy(df)
    if analysis is None:
        return

    weights = {}

    # 過大予測: スコアを最大5%ダウン
    for num, over_count, total_pred in analysis["number_over_predicted"]:
        if total_pred > 0:
            penalty = min(over_count / total_pred * 0.05, 0.05)
            weights[str(num)] = -penalty

    # 過少予測: スコアを最大5%アップ
    for num, under_count, total_app in analysis["number_under_predicted"]:
        if total_app > 0:
            bonus = min(under_count / total_app * 0.05, 0.05)
            key = str(num)
            weights[key] = weights.get(key, 0) + bonus

    try:
        _FEEDBACK_WEIGHTS_FILE.write_text(
            _json.dumps(weights, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass


def load_feedback_weights() -> dict:
    """保存されたフィードバック重みを読み込む"""
    try:
        if _FEEDBACK_WEIGHTS_FILE.exists():
            return _json.loads(_FEEDBACK_WEIGHTS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def get_feedback_summary(df: pd.DataFrame) -> str:
    """予測振り返りのサマリーテキストを生成する"""
    analysis = analyze_prediction_accuracy(df)
    if analysis is None:
        return "まだ予測履歴がありません。次回の抽選後に振り返りが表示されます。"

    lines = []
    lines.append(f"**過去 {len(analysis['rounds'])} 回分の予測振り返り**\n")
    lines.append(f"- 上位15番号の平均的中: **{analysis['avg_hits_top15']:.1f} / 7個**")
    lines.append(f"- おすすめ組の最高平均的中: **{analysis['avg_best_combo_hits']:.1f} / 7個**\n")

    for r in analysis["rounds"]:
        actual_str = ", ".join(f"{n:02d}" for n in r["actual"])
        top_hits = r["hits_in_top15"]
        best_hits = r["best_combo_hits"]
        best_str = ", ".join(f"{n:02d}" for n in r["best_combo"]) if r["best_combo"] else "-"
        lines.append(
            f"第{r['round']}回: 実際 [{actual_str}]　"
            f"上位15中 **{top_hits}個的中**　最高組 **{best_hits}個的中** [{best_str}]"
        )

    if analysis["number_over_predicted"]:
        lines.append("\n**過大予測（予測したが出にくかった番号）:**")
        for num, cnt, total in analysis["number_over_predicted"][:5]:
            lines.append(f"- {num:02d}: {cnt}/{total}回ハズレ")

    if analysis["number_under_predicted"]:
        lines.append("\n**過小予測（予測しなかったが出た番号）:**")
        for num, cnt, total in analysis["number_under_predicted"][:5]:
            lines.append(f"- {num:02d}: {cnt}/{total}回見逃し")

    fb = load_feedback_weights()
    if fb:
        adj_up = [(int(n), v) for n, v in fb.items() if v > 0]
        adj_down = [(int(n), v) for n, v in fb.items() if v < 0]
        if adj_up:
            adj_up.sort(key=lambda x: x[1], reverse=True)
            nums_str = ", ".join(f"{n:02d}(+{v*100:.1f}%)" for n, v in adj_up[:5])
            lines.append(f"\n**フィードバック補正（上方）:** {nums_str}")
        if adj_down:
            adj_down.sort(key=lambda x: x[1])
            nums_str = ", ".join(f"{n:02d}({v*100:.1f}%)" for n, v in adj_down[:5])
            lines.append(f"**フィードバック補正（下方）:** {nums_str}")

    return "\n".join(lines)


def run_backtest(df: pd.DataFrame, last_n: int = 5) -> list[dict]:
    """
    過去 last_n 回分のバックテストを実行する。
    各回について「その回の前のデータだけで予測→実際の結果と比較」を行う。
    """
    from .prediction import generate_combinations

    all_rounds = df["round"].tolist()
    if len(all_rounds) < 20:
        return []

    results = []
    test_start = max(0, len(df) - last_n)

    # 番号ごとの予測・的中・見逃し集計
    _bt_num_predicted = {}
    _bt_num_hit = {}
    _bt_num_missed = {}

    for idx in range(test_start, len(df)):
        train_df = df.iloc[:idx].copy()
        if len(train_df) < 10:
            continue

        actual_row = df.iloc[idx]
        actual = sorted(int(actual_row[f"n{i}"]) for i in range(1, 8))
        actual_set = set(actual)
        target_round = int(actual_row["round"])

        scores = _get_raw_score(train_df)
        top15 = sorted(scores, key=scores.get, reverse=True)[:15]
        hits_top15 = len(set(top15) & actual_set)

        try:
            combos = generate_combinations(train_df, n=20)
        except Exception:
            combos = []

        # 全組の的中数を計算
        combo_results = []
        best_hits = 0
        best_combo = []
        for combo in combos:
            h = len(set(combo) & actual_set)
            combo_results.append({"combo": combo, "hits": h})
            if h > best_hits:
                best_hits = h
                best_combo = combo

        # 的中数の分布
        hit_dist = Counter(cr["hits"] for cr in combo_results)
        avg_hits = sum(cr["hits"] for cr in combo_results) / len(combo_results) if combo_results else 0

        # 各番号が「おすすめに入ったか」「実際に出たか」の集計
        for combo in combos:
            for n in combo:
                _bt_num_predicted[n] = _bt_num_predicted.get(n, 0) + 1
                if n in actual_set:
                    _bt_num_hit[n] = _bt_num_hit.get(n, 0) + 1
        for n in actual:
            if not any(n in combo for combo in combos):
                _bt_num_missed[n] = _bt_num_missed.get(n, 0) + 1

        results.append({
            "round": target_round,
            "actual": actual,
            "top15": top15,
            "hits_top15": hits_top15,
            "best_combo": best_combo,
            "best_combo_hits": best_hits,
            "all_combos_count": len(combos),
            "avg_combo_hits": round(avg_hits, 2),
            "hit_distribution": dict(sorted(hit_dist.items())),
            "combos_with_3plus": sum(1 for cr in combo_results if cr["hits"] >= 3),
            "combos_with_4plus": sum(1 for cr in combo_results if cr["hits"] >= 4),
        })

    # フィードバック: バックテスト結果から重みを自動更新
    if results:
        _update_feedback_from_backtest(_bt_num_predicted, _bt_num_hit, _bt_num_missed, len(results))

    return results


def _update_feedback_from_backtest(predicted: dict, hit: dict, missed: dict, n_rounds: int):
    """
    バックテスト結果からフィードバック重みを更新する。
    - よく予測に入るが的中しない番号 → ペナルティ
    - 予測に入らないのに出る番号 → ボーナス
    """
    weights = {}
    for n in ALL_NUMBERS:
        pred_count = predicted.get(n, 0)
        hit_count = hit.get(n, 0)
        miss_count = missed.get(n, 0)

        if pred_count > 0:
            hit_rate = hit_count / pred_count
            # 的中率が低い（予測したが外れやすい）→ ペナルティ
            # 期待的中率は約 7/37 ≈ 0.189
            expected_rate = 7 / 37
            if hit_rate < expected_rate * 0.7:
                weights[str(n)] = -min((expected_rate - hit_rate) * 0.1, 0.05)
            elif hit_rate > expected_rate * 1.3:
                weights[str(n)] = min((hit_rate - expected_rate) * 0.1, 0.05)

        if miss_count > 0:
            # 予測しなかったのに出た → ボーナス
            bonus = min(miss_count / n_rounds * 0.03, 0.05)
            weights[str(n)] = weights.get(str(n), 0) + bonus

    try:
        _FEEDBACK_WEIGHTS_FILE.write_text(
            _json.dumps(weights, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass


def _get_raw_score(df: pd.DataFrame) -> dict[int, float]:
    """フィードバック重みなしの素のスコア（バックテスト用、12要因版）"""
    weights = load_optimized_weights()
    factors = _get_all_factors(df)
    streaks_raw = get_streak_stats(df)

    scores = {}
    for n in ALL_NUMBERS:
        base = sum(factors[i].get(n, 0) * weights[i] for i in range(len(weights)))
        cs = streaks_raw[n]["current_streak"]
        if cs >= 6:
            base *= 0.50
        elif cs >= 5:
            base *= 0.60
        elif cs >= 4:
            base *= 0.75
        scores[n] = base
    return scores
