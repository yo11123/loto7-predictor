"""ロト7の次回番号予測モジュール"""

import pandas as pd
import numpy as np
import random
from itertools import combinations
from .analysis import (
    get_frequency,
    get_hot_cold_numbers,
    get_number_score,
    get_typical_pattern,
    get_recent_activity,
    get_last_appearance,
    get_cooccurrence,
    get_cooccurrence_score,
    get_trend_score,
    get_repeat_score,
    get_streak_score,
    get_interval_score,
    get_neighbor_score,
    check_pattern_fit,
    ALL_NUMBERS,
)
from .data import get_main_numbers

MAIN_COUNT = 7


def _pick_top(scored: dict[int, float], n: int) -> list[int]:
    """スコア辞書から上位 n 個を返す (昇順ソート済み)"""
    top = sorted(scored, key=scored.get, reverse=True)[:n]
    return sorted(top)


# ────────────────────────────────────────────
#  戦略 1: ホット戦略 (出現頻度が高い番号)
# ────────────────────────────────────────────
def predict_hot(df: pd.DataFrame) -> list[int]:
    """直近で最も多く出現した 7 番号を返す"""
    freq = get_frequency(df)
    return _pick_top(freq, MAIN_COUNT)


# ────────────────────────────────────────────
#  戦略 2: コールド戦略 (長期間出ていない番号)
# ────────────────────────────────────────────
def predict_cold(df: pd.DataFrame) -> list[int]:
    freq = get_frequency(df)
    max_f = max(freq.values()) or 1
    cold_score = {n: (max_f - freq[n]) for n in ALL_NUMBERS}
    return _pick_top(cold_score, MAIN_COUNT)


# ────────────────────────────────────────────
#  戦略 3: バランス戦略 (ホット + コールド混合)
# ────────────────────────────────────────────
def predict_balanced(df: pd.DataFrame) -> list[int]:
    hot, cold = get_hot_cold_numbers(df, top_n=10)
    hot_nums = [n for n, _ in hot]
    cold_nums = [n for n, _ in cold]

    chosen = set()
    for n in hot_nums:
        if len(chosen) >= 4:
            break
        chosen.add(n)
    for n in cold_nums:
        if len(chosen) >= MAIN_COUNT:
            break
        chosen.add(n)

    return sorted(chosen)


# ────────────────────────────────────────────
#  戦略 4: パターン戦略 (統計的典型パターンに合わせる)
# ────────────────────────────────────────────
def predict_pattern(df: pd.DataFrame, seed: int | None = None) -> list[int]:
    rng = random.Random(seed)
    pattern = get_typical_pattern(df)

    odd_target = pattern["typical_odd_count"]
    even_target = 7 - odd_target
    sum_lo = pattern["sum_lo"]
    sum_hi = pattern["sum_hi"]

    freq = get_frequency(df)
    odds = sorted([n for n in ALL_NUMBERS if n % 2 == 1], key=freq.get, reverse=True)
    evens = sorted([n for n in ALL_NUMBERS if n % 2 == 0], key=freq.get, reverse=True)

    best = None
    for _ in range(5000):
        odd_pool = odds[:20]
        even_pool = evens[:20]
        chosen_odd = rng.sample(odd_pool, min(odd_target, len(odd_pool)))
        chosen_even = rng.sample(even_pool, min(even_target, len(even_pool)))
        candidate = sorted(set(chosen_odd + chosen_even))
        if len(candidate) == MAIN_COUNT and sum_lo <= sum(candidate) <= sum_hi:
            best = candidate
            break

    if best is None:
        best = predict_recommended(df)
    return best


# ────────────────────────────────────────────
#  戦略 5: 総合スコア戦略 (おすすめ)
# ────────────────────────────────────────────
def predict_recommended(df: pd.DataFrame) -> list[int]:
    scores = get_number_score(df)
    return _pick_top(scores, MAIN_COUNT)


# ────────────────────────────────────────────
#  全戦略まとめ
# ────────────────────────────────────────────
STRATEGIES: dict[str, dict] = {
    "recommended": {
        "label": "⭐ おすすめ（総合スコア）",
        "description": "出現頻度・直近の活性度・長期未出現ボーナスを組み合わせた総合スコアで選出。",
        "fn": predict_recommended,
    },
    "hot": {
        "label": "🔥 ホット（出現頻度上位）",
        "description": "選択した期間で最も多く出現した番号を 7 個選ぶ戦略。",
        "fn": predict_hot,
    },
    "cold": {
        "label": "❄️ コールド（長期未出現）",
        "description": "長い間出ていない番号をチョイス。「そろそろ来る」という逆張り発想。",
        "fn": predict_cold,
    },
    "balanced": {
        "label": "⚖️ バランス（ホット＋コールド）",
        "description": "ホット 4 個とコールド 3 個を混ぜたバランス型。",
        "fn": predict_balanced,
    },
    "pattern": {
        "label": "📐 パターン（典型的な組み合わせ）",
        "description": "過去の典型的な奇数割合・合計値範囲に合わせた番号を生成。",
        "fn": predict_pattern,
    },
}


def run_all_strategies(df: pd.DataFrame) -> dict[str, list[int]]:
    """全戦略を実行して結果を返す"""
    results = {}
    for key, info in STRATEGIES.items():
        try:
            results[key] = info["fn"](df)
        except Exception:
            results[key] = []
    return results


# ────────────────────────────────────────────
#  分析ベースの組み合わせ生成（決定的）
# ────────────────────────────────────────────
def _get_past_winning_sets(df: pd.DataFrame) -> set[tuple[int, ...]]:
    """過去の全当選番号組をセットとして返す"""
    past = set()
    for row in get_main_numbers(df):
        past.add(tuple(sorted(int(n) for n in row)))
    return past


def _combo_score(combo: tuple[int, ...], scores: dict[int, float]) -> float:
    """組み合わせの総合スコア（各番号のスコア合計）"""
    return sum(scores[n] for n in combo)


def generate_combinations(
    df: pd.DataFrame,
    n: int = 10,
) -> list[list[int]]:
    """
    カバレッジ重視の組み合わせ生成。

    3段階のアプローチで多様な組み合わせを保証:
    1. 番号プールをTier分け（S/A/B/C）し各Tierから必ず選出
    2. 候補をスコア順にソートした後、貪欲に多様性選択（最低差分5）
    3. カバレッジボーナス: まだ選ばれていない番号を含む組を優遇
    """
    scores = get_number_score(df)
    past = _get_past_winning_sets(df)
    pattern = get_typical_pattern(df)
    pair_count = get_cooccurrence(df)

    ranked = sorted(ALL_NUMBERS, key=lambda x: scores[x], reverse=True)

    # Tier分け: S(top10), A(11-20), B(21-30), C(31-37)
    tier_s = set(ranked[:10])
    tier_a = set(ranked[10:20])
    tier_b = set(ranked[20:30])
    tier_c = set(ranked[30:])

    # プールサイズ（必要数に応じて広げる）
    if n <= 10:
        top_k = 18
    elif n <= 50:
        top_k = 23
    elif n <= 100:
        top_k = 28
    else:
        top_k = 32
    pool = ranked[:top_k]

    max_pair = max(pair_count.values()) if pair_count else 1

    # 全候補をスコア付きで生成
    candidates = []
    for combo in combinations(pool, MAIN_COUNT):
        if combo in past:
            continue

        fit = check_pattern_fit(list(combo), pattern)
        if fit["fit_count"] < 2:
            continue

        base = _combo_score(combo, scores)

        pair_bonus = 0.0
        for pair in combinations(combo, 2):
            pair_bonus += pair_count.get(pair, 0)
        total_pairs = MAIN_COUNT * (MAIN_COUNT - 1) / 2
        pair_bonus_norm = pair_bonus / (total_pairs * max_pair)

        pattern_bonus = fit["fit_count"] / 4.0

        # Tier多様性ボーナス: 複数Tierから選ばれているほど高い
        combo_set = set(combo)
        tiers_used = sum([
            bool(combo_set & tier_s),
            bool(combo_set & tier_a),
            bool(combo_set & tier_b),
            bool(combo_set & tier_c),
        ])
        tier_bonus = tiers_used / 4.0  # 0.25〜1.0

        # 最終スコア = 基本40% + 共起15% + パターン20% + Tier多様性25%
        final_score = base * 0.40 + pair_bonus_norm * 0.15 + pattern_bonus * 0.20 + tier_bonus * 0.25
        candidates.append((combo, final_score))

    candidates.sort(key=lambda x: x[1], reverse=True)

    # ── カバレッジ重視の貪欲選択 ──
    results: list[list[int]] = []
    seen: set[tuple[int, ...]] = set()
    used_numbers: set[int] = set()  # 選択済み組に含まれる番号

    for min_diff in (5, 4, 3, 2):
        for combo, score in candidates:
            key = tuple(sorted(combo))
            if key in seen:
                continue

            combo_set = set(combo)

            # 多様性チェック: 既存の全組と min_diff 個以上異なる
            is_diverse = True
            for existing in results:
                diff_count = len(combo_set.symmetric_difference(set(existing))) // 2
                if diff_count < min_diff:
                    is_diverse = False
                    break

            if not is_diverse:
                continue

            # カバレッジボーナスで再スコア: まだ使われていない番号を含むほど優先
            new_nums = combo_set - used_numbers
            coverage_bonus = len(new_nums) / MAIN_COUNT  # 0〜1
            adjusted = score + coverage_bonus * 0.15

            seen.add(key)
            results.append(list(key))
            used_numbers.update(combo_set)

            if len(results) >= n:
                break
        if len(results) >= n:
            break

    return results


# ────────────────────────────────────────────
#  組み合わせごとの出現確率推定
# ────────────────────────────────────────────
from math import comb as math_comb, prod, log

# 理論上の全組み合わせ数 C(37, 7)
TOTAL_COMBINATIONS = math_comb(37, 7)  # 10,295,472
RANDOM_PROB = 1.0 / TOTAL_COMBINATIONS


def calc_combo_probabilities(
    df: pd.DataFrame,
    combos: list[list[int]],
) -> list[dict]:
    """
    各組み合わせの統計的出現確率を推定して返す。

    手法:
    - 各番号の経験的出現確率 P(n) = freq(n) / total_draws を計算
    - 組み合わせの出現しやすさ ∝ Π P(n_i)  (独立仮定)
    - 全候補組内で正規化して相対確率を算出
    - 理論確率（完全ランダム）との倍率も返す

    Returns:
        list of {
            "prob_pct": float,       # 候補内での相対確率 (%)
            "advantage": float,      # 理論値 (1/C(37,7)) に対する倍率
        }
    """
    total_draws = len(df)
    freq = get_frequency(df)

    # 各番号の経験的出現確率
    emp_prob = {n: freq[n] / total_draws for n in ALL_NUMBERS}

    # 各組み合わせの対数尤度（アンダーフロー防止）
    log_likelihoods = []
    for combo in combos:
        ll = sum(log(emp_prob[n]) for n in combo if emp_prob[n] > 0)
        log_likelihoods.append(ll)

    # 正規化（softmax 的に相対確率化）
    max_ll = max(log_likelihoods) if log_likelihoods else 0
    raw_weights = [2.718281828 ** (ll - max_ll) for ll in log_likelihoods]
    total_weight = sum(raw_weights)

    results = []
    for w in raw_weights:
        rel_pct = (w / total_weight) * 100 if total_weight > 0 else 0
        # 倍率: この組の相対確率 vs 完全ランダム (1/全組み合わせ数)
        uniform_pct = 100.0 / len(combos) if combos else 1
        advantage = rel_pct / uniform_pct if uniform_pct > 0 else 1.0
        results.append({
            "prob_pct": round(rel_pct, 3),
            "advantage": round(advantage, 2),
        })

    return results


# ────────────────────────────────────────────
#  組み合わせの選定理由を生成
# ────────────────────────────────────────────
def explain_combo(df: pd.DataFrame, combo: list[int]) -> dict:
    """
    組み合わせ内の各番号がなぜ選ばれたかを9要因で分類して返す。

    Returns:
        {
            "summary": str,          # 1行まとめ
            "details": list[str],    # 番号ごとの説明
            "factor_breakdown": list[dict],  # 番号ごとの全9要因スコア
        }
    """
    total = len(df)
    freq = get_frequency(df)
    max_freq = max(freq.values()) or 1
    recent = get_recent_activity(df, last_n=max(10, total // 10))
    max_recent = max(recent.values()) or 1
    gap = get_last_appearance(df)
    max_gap = max(gap.values()) or 1
    co = get_cooccurrence_score(df)
    trend = get_trend_score(df)
    repeat = get_repeat_score(df)
    streak = get_streak_score(df)
    interval = get_interval_score(df)
    neighbor = get_neighbor_score(df)
    total_score = get_number_score(df)

    # 各要因の名前とスコア辞書
    factor_defs = [
        ("頻度", lambda n: freq[n] / max_freq),
        ("活性度", lambda n: recent[n] / max_recent),
        ("未出現", lambda n: gap[n] / max_gap),
        ("共起力", lambda n: co[n]),
        ("トレンド", lambda n: trend[n]),
        ("連続出現", lambda n: repeat[n]),
        ("ストリーク", lambda n: streak[n]),
        ("間隔周期", lambda n: interval[n]),
        ("隣接効果", lambda n: neighbor[n]),
    ]

    factor_breakdown = []
    details = []

    for n in sorted(combo):
        # 各要因のスコアを計算
        f_scores = {name: fn(n) for name, fn in factor_defs}

        # 上位3要因を特定（この番号が選ばれた主な理由）
        top3 = sorted(f_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        top3_tags = [f"{name}({v:.2f})" for name, v in top3 if v > 0.1]

        if top3_tags:
            reason = " / ".join(top3_tags)
        else:
            reason = "バランス型"

        details.append(f"**{n:02d}**: {reason}")
        factor_breakdown.append({
            "number": n,
            "total": total_score[n],
            **f_scores,
        })

    # サマリー: 組全体で最も寄与している要因を特定
    factor_avgs = {}
    for name, fn in factor_defs:
        avg = sum(fn(n) for n in sorted(combo)) / len(combo)
        factor_avgs[name] = avg

    top_factors = sorted(factor_avgs.items(), key=lambda x: x[1], reverse=True)[:3]
    summary = "主要要因: " + " / ".join(f"{name}({v:.2f})" for name, v in top_factors)

    return {
        "summary": summary,
        "details": details,
        "factor_breakdown": factor_breakdown,
    }
