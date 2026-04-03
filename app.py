"""ロト7 次回予測アプリ — メインファイル"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from modules.data import fetch_loto7_results, parse_uploaded_csv, refresh_results, get_main_numbers
from modules.analysis import (
    get_frequency,
    get_frequency_df,
    get_hot_cold_numbers,
    get_pattern_stats,
    get_last_appearance,
    get_number_score,
    get_recent_activity,
    get_top_pairs,
    get_trending_numbers,
    get_repeat_stats,
    get_repeat_score,
    get_streak_stats,
    get_streak_score,
    get_recent_draws_text,
    get_interval_score,
    get_interval_stats,
    get_neighbor_score,
    get_neighbor_numbers,
    get_cooccurrence_score,
    get_trend_score,
    ALL_NUMBERS,
)
from modules.prediction import (
    STRATEGIES,
    run_all_strategies,
    generate_combinations,
    calc_combo_probabilities,
    explain_combo,
)

# ──────────────────────────────────────────────
#  ページ設定
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="ロト7 次回予測",
    page_icon="🎯",
    layout="wide",
)

# ══════════════════════════════════════════════
#  カスタム CSS
# ══════════════════════════════════════════════
st.markdown(
    """
<style>
/* ── 全体背景 ── */
.stApp {
    background: linear-gradient(160deg, #0a0f1e 0%, #0f172a 40%, #101d30 100%);
}

/* ── サイドバー ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1425 0%, #111c33 100%);
    border-right: 1px solid #1e3050;
}

/* ── タブ ── */
button[data-baseweb="tab"] {
    font-size: 15px !important;
    font-weight: 600 !important;
    padding: 10px 24px !important;
    border-radius: 10px 10px 0 0 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #1e3a5f 0%, #1a2d4a 100%) !important;
    border-bottom: 2px solid #60a5fa !important;
}

/* ── タブパネル内のコンテンツを常に不透明に ── */
div[data-baseweb="tab-panel"] {
    opacity: 1 !important;
}
div[data-baseweb="tab-panel"] * {
    opacity: inherit;
}
/* タブ内の全テキストを明るく */
div[data-baseweb="tab-panel"] p,
div[data-baseweb="tab-panel"] span,
div[data-baseweb="tab-panel"] div,
div[data-baseweb="tab-panel"] label,
div[data-baseweb="tab-panel"] h1,
div[data-baseweb="tab-panel"] h2,
div[data-baseweb="tab-panel"] h3,
div[data-baseweb="tab-panel"] td,
div[data-baseweb="tab-panel"] th,
div[data-baseweb="tab-panel"] li {
    color: #e2e8f0 !important;
}
/* Streamlit markdown/caption の色を強制 */
div[data-baseweb="tab-panel"] .stMarkdown,
div[data-baseweb="tab-panel"] .stMarkdown p {
    color: #e2e8f0 !important;
    opacity: 1 !important;
}
div[data-baseweb="tab-panel"] small,
div[data-baseweb="tab-panel"] .stCaption,
div[data-baseweb="tab-panel"] .stCaption p {
    color: #94a3b8 !important;
    opacity: 1 !important;
}

/* ── メトリックカード ── */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #131f36 0%, #172340 100%);
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 14px 16px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.3);
}
div[data-testid="stMetric"] label {
    color: #64748b !important;
    font-size: 12px !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: #60a5fa !important;
    font-weight: 700 !important;
}

/* ── エキスパンダー ── */
div[data-testid="stExpander"] {
    background: linear-gradient(135deg, #111b2e 0%, #152035 100%);
    border: 1px solid #1e3050;
    border-radius: 12px;
    overflow: hidden;
}
div[data-testid="stExpander"] summary {
    font-weight: 600;
    color: #94a3b8;
}
div[data-testid="stExpander"] summary:hover {
    color: #e2e8f0;
}

/* ── 区切り線 ── */
hr {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, #1e3a5f, transparent);
    margin: 1.5rem 0;
}

/* ── ボタン ── */
button[kind="primary"] {
    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%) !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 8px rgba(37,99,235,0.3) !important;
    transition: all 0.2s ease !important;
}
button[kind="primary"]:hover {
    box-shadow: 0 4px 16px rgba(37,99,235,0.5) !important;
    transform: translateY(-1px);
}

/* ── data_editor テーブル ── */
div[data-testid="stDataEditor"] {
    border: 1px solid #1e3050;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}

/* ── dataframe ── */
div[data-testid="stDataFrame"] {
    border: 1px solid #1e3050;
    border-radius: 12px;
    overflow: hidden;
}

/* ── カスタムカードクラス ── */
.glass-card {
    background: linear-gradient(135deg,
        rgba(15,25,50,0.8) 0%,
        rgba(20,35,60,0.6) 100%);
    border: 1px solid rgba(96,165,250,0.15);
    border-radius: 16px;
    padding: 20px 24px;
    margin: 8px 0;
    backdrop-filter: blur(10px);
    box-shadow: 0 4px 24px rgba(0,0,0,0.2);
}
.glass-card-accent {
    background: linear-gradient(135deg,
        rgba(37,99,235,0.12) 0%,
        rgba(59,130,246,0.06) 100%);
    border: 1px solid rgba(96,165,250,0.25);
    border-radius: 16px;
    padding: 20px 24px;
    margin: 8px 0;
    box-shadow: 0 4px 24px rgba(37,99,235,0.1);
}
.section-title {
    font-size: 1.3rem;
    font-weight: 700;
    color: #e2e8f0;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-subtitle {
    font-size: 0.82rem;
    color: #64748b;
    margin-bottom: 12px;
}
.num-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 46px;
    height: 46px;
    border-radius: 12px;
    font-size: 19px;
    font-weight: 800;
    margin: 3px;
    letter-spacing: 1px;
    text-shadow: 0 1px 2px rgba(0,0,0,0.5);
}
/* 1-9: 青 */
.num-r1 {
    background: linear-gradient(145deg, #1d4ed8, #2563eb);
    color: #ffffff;
    border: 2px solid #60a5fa;
    box-shadow: 0 2px 8px rgba(37,99,235,0.4);
}
/* 10-19: 緑 */
.num-r2 {
    background: linear-gradient(145deg, #15803d, #16a34a);
    color: #ffffff;
    border: 2px solid #4ade80;
    box-shadow: 0 2px 8px rgba(22,163,74,0.4);
}
/* 20-29: オレンジ */
.num-r3 {
    background: linear-gradient(145deg, #c2410c, #ea580c);
    color: #ffffff;
    border: 2px solid #fb923c;
    box-shadow: 0 2px 8px rgba(234,88,12,0.4);
}
/* 30-37: 紫 */
.num-r4 {
    background: linear-gradient(145deg, #7e22ce, #9333ea);
    color: #ffffff;
    border: 2px solid #c084fc;
    box-shadow: 0 2px 8px rgba(147,51,234,0.4);
}
.tag-hot     { background:#7f1d1d; color:#fca5a5; padding:2px 8px; border-radius:6px; font-size:12px; font-weight:600; }
.tag-cold    { background:#1e3a5f; color:#93c5fd; padding:2px 8px; border-radius:6px; font-size:12px; font-weight:600; }
.tag-recent  { background:#14532d; color:#86efac; padding:2px 8px; border-radius:6px; font-size:12px; font-weight:600; }
.tag-gap     { background:#713f12; color:#fde68a; padding:2px 8px; border-radius:6px; font-size:12px; font-weight:600; }
.tag-neutral { background:#334155; color:#94a3b8; padding:2px 8px; border-radius:6px; font-size:12px; font-weight:600; }
.purchased-card {
    background: linear-gradient(135deg, rgba(20,83,45,0.2), rgba(22,78,40,0.1));
    border: 1px solid rgba(34,197,94,0.3);
    border-radius: 10px;
    padding: 10px 16px;
    margin: 4px 0;
    font-family: monospace;
    font-size: 15px;
    color: #86efac;
}
.score-rank {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #0f172a;
    border: 1px solid #1e3050;
    border-radius: 8px;
    padding: 4px 10px;
    margin: 2px;
    font-size: 13px;
}
.score-rank .num { font-weight: 700; color: #e2e8f0; min-width: 24px; }
.score-rank .bar { color: #3b82f6; letter-spacing: -2px; }
.score-rank .val { color: #64748b; font-size: 11px; }
</style>
""",
    unsafe_allow_html=True,
)


def _num_class(n: int) -> str:
    """番号の範囲に応じた CSS クラスを返す"""
    if n <= 9:
        return "num-r1"
    elif n <= 19:
        return "num-r2"
    elif n <= 29:
        return "num-r3"
    else:
        return "num-r4"


def _num_badge(n: int) -> str:
    """番号バッジの HTML を返す"""
    return f'<span class="num-badge {_num_class(n)}">{n:02d}</span>'


def _num_badges_with_consec(nums: list[int]) -> str:
    """
    番号リストをバッジ HTML に変換。
    連続する番号（差が1）のグループを細い線で囲む。
    """
    sorted_nums = sorted(nums)

    # 連続グループを検出
    groups: list[list[int]] = []
    current_group = [sorted_nums[0]]
    for i in range(1, len(sorted_nums)):
        if sorted_nums[i] == sorted_nums[i - 1] + 1:
            current_group.append(sorted_nums[i])
        else:
            groups.append(current_group)
            current_group = [sorted_nums[i]]
    groups.append(current_group)

    html = ""
    for group in groups:
        if len(group) >= 2:
            # 連続グループ → 囲み線
            inner = "".join(_num_badge(n) for n in group)
            html += (
                f'<span style="display:inline-flex;align-items:center;'
                f'border:2px solid rgba(250,204,21,0.7);border-radius:14px;'
                f'padding:2px 3px;margin:1px 2px;'
                f'box-shadow:0 0 8px rgba(250,204,21,0.2)">'
                f"{inner}</span>"
            )
        else:
            html += _num_badge(group[0])
    return html


# ── ヘッダー ──
st.markdown(
    '<div style="text-align:center;padding:10px 0 0">'
    '<span style="font-size:2.5rem">🎯</span>'
    '<h1 style="margin:0;font-size:2rem;background:linear-gradient(90deg,#60a5fa,#a78bfa);'
    '-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:800">'
    "ロト7 次回予測</h1>"
    '<p style="color:#64748b;font-size:0.85rem;margin-top:4px">'
    "統計分析に基づく番号予測ツール（娯楽目的）</p>"
    '<div style="display:flex;justify-content:center;gap:12px;margin-top:8px;flex-wrap:wrap">'
    '<span class="num-badge num-r1" style="width:auto;height:auto;padding:4px 12px;font-size:12px">01-09</span>'
    '<span class="num-badge num-r2" style="width:auto;height:auto;padding:4px 12px;font-size:12px">10-19</span>'
    '<span class="num-badge num-r3" style="width:auto;height:auto;padding:4px 12px;font-size:12px">20-29</span>'
    '<span class="num-badge num-r4" style="width:auto;height:auto;padding:4px 12px;font-size:12px">30-37</span>'
    "</div></div>",
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
#  サイドバー：データ取得
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div class="section-title">⚙️ 設定</div>',
        unsafe_allow_html=True,
    )
    data_source = st.radio(
        "データソース",
        ["自動取得（Web）", "CSV アップロード"],
        index=0,
    )

    df_raw = None

    if data_source == "自動取得（Web）":
        col_fetch, col_refresh = st.columns(2)
        with col_fetch:
            with st.spinner("取得中..."):
                df_raw = fetch_loto7_results()
        with col_refresh:
            if st.button("🔄 更新", use_container_width=True):
                with st.spinner("最新データを取得中..."):
                    df_raw = refresh_results()
                    # 組み合わせ・チェック・カスタム番号を全リセット
                    keys_to_clear = [
                        k for k in st.session_state
                        if k.startswith("chk_") or k in ("combos", "_combo_cache_key", "custom_nums")
                    ]
                    for k in keys_to_clear:
                        del st.session_state[k]
                    st.rerun()
        if df_raw is None:
            st.error("自動取得に失敗。CSV をお試しください。")
    else:
        uploaded = st.file_uploader(
            "CSV をアップロード",
            type=["csv"],
            help="列: 回号, 抽選日, 第1〜第7数字, ボーナス1, ボーナス2",
        )
        if uploaded:
            df_raw = parse_uploaded_csv(uploaded)
            if df_raw is None or df_raw.empty:
                st.error("CSV の読み込みに失敗しました。")

    st.markdown("---")

    if df_raw is not None and not df_raw.empty:
        max_rounds = len(df_raw)
        recent_n = st.slider(
            "分析に使う直近の回数",
            min_value=10,
            max_value=max_rounds,
            value=max_rounds,
            step=1,
        )
        st.metric("総データ数", f"{max_rounds} 回")
        st.metric("最新回", f"第 {df_raw['round'].max()} 回")
        if "date" in df_raw.columns and not df_raw["date"].dropna().empty:
            st.metric("最新抽選日", str(df_raw["date"].dropna().iloc[-1])[:10])
    else:
        recent_n = 100

    st.markdown("---")
    st.markdown('<div class="section-title" style="font-size:0.9rem">🤖 Gemini AI 設定</div>', unsafe_allow_html=True)

    # APIキーの保存/読み込み
    import json as _json
    from pathlib import Path as _Path
    _key_file = _Path(__file__).parent / ".api_keys.json"

    def _load_saved_key() -> str:
        try:
            if _key_file.exists():
                data = _json.loads(_key_file.read_text(encoding="utf-8"))
                return data.get("gemini_key", "")
        except Exception:
            pass
        return ""

    def _save_key(key: str):
        try:
            _key_file.write_text(
                _json.dumps({"gemini_key": key}, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception:
            pass

    # 初回起動時にファイルから読み込み
    if "gemini_key" not in st.session_state:
        st.session_state["gemini_key"] = _load_saved_key()

    gemini_key = st.text_input(
        "Gemini API Key", type="password", key="gemini_key",
        help="AI相談タブのチャット機能に必要です（Google AI Studio で無料取得可）",
    )

    if gemini_key:
        if gemini_key != _load_saved_key():
            _save_key(gemini_key)
            st.caption("✅ APIキーを保存しました")
        else:
            st.caption("🔑 保存済み")
    elif _load_saved_key():
        st.caption("⚠️ キーがクリアされました")

if df_raw is None or df_raw.empty:
    st.warning(
        "抽選結果データが取得できていません。\n\n"
        "**CSV ファイルを手動でアップロードしてください。**\n\n"
        "期待するフォーマット（ヘッダー行あり）:\n"
        "```\n回号,抽選日,第1数字,第2数字,...,第7数字,ボーナス1,ボーナス2\n```"
    )
    st.stop()

df = df_raw.tail(recent_n).reset_index(drop=True)
next_round = int(df_raw["round"].max()) + 1

# ── チェック状態の永続化 ──
_checks_file = _Path(__file__).parent / ".purchased_checks.json"

def _load_checks() -> dict:
    """ファイルからチェック状態を読み込む"""
    try:
        if _checks_file.exists():
            return _json.loads(_checks_file.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}

def _save_checks():
    """現在のチェック状態をファイルに保存"""
    try:
        checks = {}
        for k, v in st.session_state.items():
            if k.startswith("chk_") and v:
                checks[k] = True
        # ラウンド情報も保存して、新抽選時にリセット判定
        checks["_round"] = int(df_raw["round"].max())
        _checks_file.write_text(
            _json.dumps(checks, ensure_ascii=False), encoding="utf-8"
        )
    except Exception:
        pass

# ── 起動時にチェック状態を復元 + 抽選更新時リセット ──
_current_latest = int(df_raw["round"].max())

if "_checks_loaded" not in st.session_state:
    # 初回起動: ファイルからチェック状態を復元
    saved = _load_checks()
    saved_round = saved.pop("_round", 0)

    if saved_round == _current_latest:
        # 同じラウンド → チェックを復元
        for k, v in saved.items():
            if k.startswith("chk_"):
                st.session_state[k] = v
    else:
        # 違うラウンド → リセット（復元しない）、キャッシュもクリア
        for k in list(st.session_state.keys()):
            if k.startswith("chk_") or k in ("combos", "_combo_cache_key", "custom_nums"):
                del st.session_state[k]
        _save_checks()

    st.session_state["_last_known_round"] = _current_latest
    st.session_state["_checks_loaded"] = True

elif st.session_state.get("_last_known_round", 0) != _current_latest:
    # セッション中に新しい抽選回が追加された場合
    keys_to_clear = [
        k for k in list(st.session_state.keys())
        if k.startswith("chk_") or k in ("combos", "_combo_cache_key", "custom_nums")
    ]
    for k in keys_to_clear:
        del st.session_state[k]
    st.session_state["_last_known_round"] = _current_latest
    _save_checks()

# ── 前回の当選番号を表示 ──
_last_row = df_raw.iloc[-1]
_last_round = int(_last_row["round"])
_last_date = str(_last_row.get("date", ""))[:10] if "date" in _last_row else ""
_last_main = sorted(int(_last_row[f"n{i}"]) for i in range(1, 8))
_last_bonus = []
for _bc in ["b1", "b2"]:
    if _bc in _last_row and pd.notna(_last_row[_bc]):
        _last_bonus.append(int(_last_row[_bc]))

_last_badges = _num_badges_with_consec(_last_main)
_bonus_badges = "".join(
    f'<span class="num-badge" style="background:linear-gradient(145deg,#374151,#4b5563);'
    f'color:#d1d5db;border:2px dashed #6b7280;opacity:0.7">{b:02d}</span>'
    for b in _last_bonus
)

st.markdown(
    f'<div class="glass-card" style="text-align:center">'
    f'<div style="color:#64748b;font-size:13px;margin-bottom:6px">'
    f'前回　第 {_last_round} 回（{_last_date}）</div>'
    f'<div style="display:flex;justify-content:center;align-items:center;gap:8px;flex-wrap:wrap">'
    f'{_last_badges}'
    f'{"<span style=color:#64748b;font-size:12px;margin:0_8px>＋ボーナス</span>" + _bonus_badges if _last_bonus else ""}'
    f'</div></div>',
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
#  タブ構成
# ──────────────────────────────────────────────
tab_pred, tab_ranking, tab_analysis, tab_history, tab_sim, tab_ai = st.tabs(
    ["🎯 予測", "🏆 要因別ランキング", "📊 分析", "📋 過去の結果", "🎰 模擬抽選", "🤖 AI相談"]
)

# ══════════════════════════════════════════════
#  タブ1: 予測
# ══════════════════════════════════════════════
with tab_pred:
    st.markdown(
        f'<div class="glass-card-accent">'
        f'<div class="section-title">第 {next_round} 回　予測番号</div>'
        f'<div class="section-subtitle">直近 {recent_n} 回（全 {len(df_raw)} 回中）のデータをもとに分析</div>'
        f"</div>",
        unsafe_allow_html=True,
    )

    all_results = run_all_strategies(df)
    scores = get_number_score(df)
    ranked_nums = sorted(ALL_NUMBERS, key=lambda x: scores[x], reverse=True)

    # ── 番号別スコアランキング ──
    with st.expander("📊 番号別スコアランキング（予測の根拠）"):
        rank_html = '<div style="display:flex;flex-wrap:wrap;gap:4px">'
        for i, n in enumerate(ranked_nums):
            pct = scores[n] * 100
            bar_len = max(1, int(pct / 5))
            bar = "█" * bar_len
            rank_html += (
                f'<div class="score-rank">'
                f'<span class="num">{n:02d}</span>'
                f'<span class="bar">{bar}</span>'
                f'<span class="val">{pct:.0f}</span>'
                f"</div>"
            )
        rank_html += "</div>"
        st.markdown(rank_html, unsafe_allow_html=True)

    st.markdown("")

    # ── おすすめ組み合わせ ──
    st.markdown(
        '<div class="glass-card">'
        '<div class="section-title">⭐ おすすめの組み合わせ</div>'
        '<div class="section-subtitle">'
        "スコア上位番号の全組み合わせからランキング。過去の当選組は自動除外済み。</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    with st.expander("📖 各数値の見方"):
        st.markdown(
            "| 列 | 意味 |\n"
            "|---|---|\n"
            "| **スコア** | 9つの分析要因（①出現頻度 ②直近活性度 ③長期未出現 ④共起力 ⑤トレンド "
            "⑥連続出現率 ⑦ストリーク ⑧出現間隔周期 ⑨隣接数字効果）を加重合算した総合評価。"
            "7つの番号のスコア合計値で、**高いほど統計的に出やすい組み合わせ**。 |\n"
            "| **確率(%)** | 表示中の候補の中で、この組が出る相対的な確率。"
            "各番号の過去の出現率を掛け合わせて算出。**候補内の合計が100%**になる。 |\n"
            "| **優位倍率** | 全候補が均等に出ると仮定した場合に対して、"
            "この組がどれだけ有利かを示す倍率。"
            "**1.00x＝平均並み、>1.00x＝出やすい、<1.00x＝出にくい**。 |\n"
        )

    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        combo_count = st.number_input(
            "表示する組み合わせ数",
            min_value=1,
            max_value=200,
            value=10,
            step=1,
        )
    with col_opt2:
        sort_options = {
            "スコア（高い順）": ("スコア", False),
            "スコア（低い順）": ("スコア", True),
            "確率（高い順）": ("確率(%)", False),
            "確率（低い順）": ("確率(%)", True),
            "優位倍率（高い順）": ("優位倍率", False),
            "優位倍率（低い順）": ("優位倍率", True),
            "No.（昇順）": ("No.", True),
        }
        sort_choice = st.selectbox("並び替え", list(sort_options.keys()), index=0)

    # キャッシュキーにバージョンを含めてコード変更時に再計算
    _ANALYSIS_VERSION = 9  # 分析要因数が変わったらインクリメント
    cache_key_data = (len(df_raw), recent_n, combo_count, _ANALYSIS_VERSION)
    if (
        "combos" not in st.session_state
        or st.session_state.get("_combo_cache_key") != cache_key_data
    ):
        st.session_state["combos"] = generate_combinations(df, n=combo_count)
        st.session_state["_combo_cache_key"] = cache_key_data

    combos = st.session_state["combos"]

    # 予測結果を常に保存（振り返り用 — キャッシュ外で実行）
    from modules.analysis import save_predictions, get_number_score as _gns, update_feedback_weights
    if combos and st.session_state.get("_prediction_saved_round") != next_round:
        _scores_for_save = _gns(df)
        save_predictions(next_round, combos, _scores_for_save)
        update_feedback_weights(df)
        st.session_state["_prediction_saved_round"] = next_round

    # カスタム番号変更を管理する session_state
    if "custom_nums" not in st.session_state:
        st.session_state["custom_nums"] = {}

    # ── 右クリック入れ替えのクエリパラメータ処理 ──
    qp = st.query_params
    if "swap" in qp:
        try:
            parts = qp["swap"].split("-")
            s_no, s_from, s_to = int(parts[0]), int(parts[1]), int(parts[2])
            # 現在の組を取得
            if s_no in st.session_state["custom_nums"]:
                cur = st.session_state["custom_nums"][s_no]
            elif 1 <= s_no <= len(combos):
                cur = sorted(combos[s_no - 1])
            else:
                cur = None
            if cur and s_from in cur and s_to not in cur and 1 <= s_to <= 37:
                new_nums = sorted(s_to if n == s_from else n for n in cur)
                st.session_state["custom_nums"][s_no] = new_nums
        except (ValueError, IndexError):
            pass
        st.query_params.clear()
        st.rerun()

    if combos:
        # カスタム変更を反映した組み合わせリスト
        display_combos = []
        for i, nums in enumerate(combos, 1):
            if i in st.session_state["custom_nums"]:
                display_combos.append(st.session_state["custom_nums"][i])
            else:
                display_combos.append(sorted(nums))

        prob_data = calc_combo_probabilities(df, display_combos)

        combo_rows = []
        for i, (nums, prob) in enumerate(zip(display_combos, prob_data), 1):
            row = {"No.": i}
            for j, n in enumerate(sorted(nums), 1):
                row[f"第{j}"] = n
            row["確率(%)"] = prob["prob_pct"]
            row["優位倍率"] = prob["advantage"]
            row["スコア"] = round(sum(scores.get(n, 0) for n in nums), 2)
            combo_rows.append(row)
        combo_df = pd.DataFrame(combo_rows)

        sort_col, sort_asc = sort_options[sort_choice]
        combo_df = combo_df.sort_values(sort_col, ascending=sort_asc).reset_index(
            drop=True
        )

        if st.session_state["custom_nums"]:
            if st.button("🔄 番号変更を全てリセット"):
                st.session_state["custom_nums"] = {}
                st.rerun()

        # ── 色付きテーブル（各行にチェック + 番号クリックで入れ替え） ──
        # st.fragment で囲んでチェック操作時の再描画を高速化
        @st.fragment
        def _render_combo_list(_combo_df, _scores_dict):
            _purchased = []
            for _, row in _combo_df.iterrows():
                no = int(row["No."])
                nums = [int(row[f"第{j}"]) for j in range(1, 8)]
                is_custom = no in st.session_state.get("custom_nums", {})
                badges = _num_badges_with_consec(nums)
                custom_mark = '<span style="color:#fbbf24;font-size:11px;margin-left:4px">✎変更済</span>' if is_custom else ""
                stats_text = (
                    f'<span style="color:#94a3b8;font-size:13px;margin-left:8px">'
                    f'確率 {row["確率(%)"]:.3f}%　'
                    f'優位 {row["優位倍率"]:.2f}x　'
                    f'スコア {row["スコア"]:.2f}</span>'
                )

                _already_checked = st.session_state.get(f"chk_{no}", False)
                _row_opacity = "0.35" if _already_checked else "1.0"
                _row_extra = ""
                if _already_checked:
                    _row_extra = '<span style="color:#22c55e;font-size:11px;margin-left:6px;font-weight:600">✓ 購入済</span>'

                col_chk, col_nums, col_edit = st.columns([0.4, 8.6, 1])
                with col_chk:
                    chk = st.checkbox("", key=f"chk_{no}", label_visibility="collapsed")
                with col_nums:
                    st.markdown(
                        f'<div style="display:flex;align-items:center;flex-wrap:wrap;gap:2px;margin-top:2px;opacity:{_row_opacity}">'
                        f'<span style="color:#e2e8f0;font-weight:700;min-width:52px">No.{no}</span>'
                        f'{badges}{custom_mark}{_row_extra}{stats_text}</div>',
                        unsafe_allow_html=True,
                    )
                with col_edit:
                    with st.popover("✏️", use_container_width=True):
                        st.markdown(f"**No.{no} の番号を入れ替え**")
                        swap_from = st.selectbox(
                            "変更する番号", nums,
                            key=f"sf_{no}",
                            format_func=lambda x: f"{x:02d}",
                        )
                        available = sorted(n for n in ALL_NUMBERS if n not in nums)
                        swap_to = st.selectbox(
                            "新しい番号", available,
                            key=f"st_{no}",
                            format_func=lambda x: f"{x:02d}",
                        )
                        if st.button("入れ替え", key=f"sb_{no}", type="primary", use_container_width=True):
                            new_nums = sorted(swap_to if n == swap_from else n for n in nums)
                            if "custom_nums" not in st.session_state:
                                st.session_state["custom_nums"] = {}
                            st.session_state["custom_nums"][no] = new_nums
                            st.rerun()
                if chk:
                    _purchased.append((no, nums))

            # チェック状態をファイルに保存
            _save_checks()
            st.session_state["_purchased_nos"] = _purchased

        _render_combo_list(combo_df, scores)
        purchased_nos = st.session_state.get("_purchased_nos", [])

        # ── 選定理由 ──
        with st.expander("🔍 各組み合わせの選定理由", expanded=False):
            for idx, nums in enumerate(combos, 1):
                exp = explain_combo(df, nums)
                badges = _num_badges_with_consec(nums)

                st.markdown(
                    f'<div style="margin:8px 0">'
                    f'<strong style="color:#60a5fa">No.{idx}</strong>　{badges}'
                    f"</div>",
                    unsafe_allow_html=True,
                )

                # タグ表示
                tags_html = ""
                for d_line in exp["details"]:
                    num_str = d_line.split("**")[1] if "**" in d_line else ""
                    desc = d_line.split(":")[-1].strip() if ":" in d_line else d_line
                    parts = desc.split(" / ")
                    for p in parts:
                        if "ホット" in p:
                            tags_html += f'<span class="tag-hot">{num_str} {p}</span> '
                        elif "コールド" in p:
                            tags_html += f'<span class="tag-cold">{num_str} {p}</span> '
                        elif "直近活発" in p:
                            tags_html += f'<span class="tag-recent">{num_str} {p}</span> '
                        elif "未出現" in p:
                            tags_html += f'<span class="tag-gap">{num_str} {p}</span> '
                        else:
                            tags_html += f'<span class="tag-neutral">{num_str} {p}</span> '

                st.markdown(
                    f'<div style="margin:0 0 12px 20px;line-height:2">{tags_html}</div>',
                    unsafe_allow_html=True,
                )

                if idx < len(combos):
                    st.markdown(
                        '<hr style="margin:4px 0;opacity:0.3">',
                        unsafe_allow_html=True,
                    )

        # ── 購入済みまとめ ──
        if purchased_nos:
            st.markdown(
                f'<div class="glass-card">'
                f'<div class="section-title">🛒 購入済み: {len(purchased_nos)} 組</div>'
                f"</div>",
                unsafe_allow_html=True,
            )
            for no, nums in purchased_nos:
                badges = _num_badges_with_consec(nums)
                st.markdown(
                    f'<div class="purchased-card" style="display:flex;align-items:center;gap:4px">'
                    f'<span style="min-width:50px;font-weight:700">No.{no}</span>{badges}</div>',
                    unsafe_allow_html=True,
                )
    else:
        st.warning("組み合わせを生成できませんでした。分析対象の回数を増やしてみてください。")

    # ── 予測精度バックテスト ──
    st.markdown("")
    from modules.analysis import (
        run_backtest, get_feedback_summary, analyze_prediction_accuracy,
        optimize_weights, load_optimized_weights, FACTOR_NAMES, DEFAULT_WEIGHTS,
    )

    # ── 重み最適化 ──
    with st.expander("🧠 重みの自動最適化（12要因の配分を学習）", expanded=False):
        st.caption(
            "過去データでバックテストを繰り返し、12要因の最適な重み配分を自動で発見します。"
            "初回は数十秒かかりますが、結果は保存されて次回以降の予測に反映されます。"
        )

        _opt_rounds = st.slider("学習に使う回数", 5, 30, 15, key="opt_rounds")

        if st.button("最適化を実行", key="btn_opt", type="primary"):
            with st.spinner(f"直近 {_opt_rounds} 回で12要因の重みを最適化中...（数十秒かかります）"):
                opt_w = optimize_weights(df, test_rounds=_opt_rounds)

            _factor_labels = {
                "freq": "頻度", "recent": "活性度", "gap": "未出現",
                "cooccurrence": "共起", "trend": "トレンド", "repeat": "連続出現",
                "streak": "ストリーク", "interval": "周期性", "neighbor": "隣接効果",
                "conditional": "条件付確率", "pattern_match": "パターン認識", "ensemble": "合議制",
            }
            opt_html = '<div style="display:flex;flex-wrap:wrap;gap:6px;margin:8px 0">'
            for name, w in zip(FACTOR_NAMES, opt_w):
                label = _factor_labels.get(name, name)
                pct = w * 100
                bar_w = int(pct * 4)
                opt_html += (
                    f'<div style="background:#1e293b;border:1px solid #334155;border-radius:6px;padding:6px 10px;min-width:120px">'
                    f'<div style="font-size:11px;color:#64748b">{label}</div>'
                    f'<div style="display:flex;align-items:center;gap:6px">'
                    f'<div style="flex:1;background:#0f172a;border-radius:3px;height:6px;overflow:hidden">'
                    f'<div style="width:{bar_w}%;height:100%;background:#60a5fa;border-radius:3px"></div></div>'
                    f'<span style="font-size:13px;font-weight:700;color:#e2e8f0;min-width:40px">{pct:.1f}%</span>'
                    f'</div></div>'
                )
            opt_html += '</div>'
            st.markdown(opt_html, unsafe_allow_html=True)
            st.success("最適化完了。次回の予測に自動反映されます。")

        # 現在の重みを表示
        _cur_w = load_optimized_weights()
        _is_default = _cur_w == DEFAULT_WEIGHTS
        st.markdown(f"現在の重み: {'**デフォルト**（未最適化）' if _is_default else '**最適化済み**'}")

    with st.expander("📊 予測精度の検証（過去データでバックテスト）", expanded=False):
        st.caption("過去の抽選を「予測→結果比較」でシミュレーションし、分析の精度を検証します。")

        _bt_n = st.slider("バックテストする回数", 3, 20, 5, key="bt_n")

        if st.button("バックテスト実行", key="btn_bt"):
            with st.spinner(f"直近 {_bt_n} 回分のバックテスト中..."):
                bt_results = run_backtest(df, last_n=_bt_n)

            if bt_results:
                avg_top15 = sum(r["hits_top15"] for r in bt_results) / len(bt_results)
                avg_best = sum(r["best_combo_hits"] for r in bt_results) / len(bt_results)
                avg_all = sum(r["avg_combo_hits"] for r in bt_results) / len(bt_results)
                total_3plus = sum(r["combos_with_3plus"] for r in bt_results)
                total_4plus = sum(r["combos_with_4plus"] for r in bt_results)
                total_combos = sum(r["all_combos_count"] for r in bt_results)

                st.markdown(
                    f'<div class="glass-card">'
                    f'<div style="display:flex;gap:24px;justify-content:center;flex-wrap:wrap">'
                    f'<div style="text-align:center">'
                    f'<div style="color:#64748b;font-size:11px">上位15番号<br>平均的中</div>'
                    f'<div style="font-size:1.6rem;font-weight:700;color:#60a5fa">{avg_top15:.1f}<span style="font-size:0.8rem;color:#64748b"> / 7</span></div>'
                    f'</div>'
                    f'<div style="text-align:center">'
                    f'<div style="color:#64748b;font-size:11px">最高組<br>平均的中</div>'
                    f'<div style="font-size:1.6rem;font-weight:700;color:#a78bfa">{avg_best:.1f}<span style="font-size:0.8rem;color:#64748b"> / 7</span></div>'
                    f'</div>'
                    f'<div style="text-align:center">'
                    f'<div style="color:#64748b;font-size:11px">全組<br>平均的中</div>'
                    f'<div style="font-size:1.6rem;font-weight:700;color:#34d399">{avg_all:.2f}<span style="font-size:0.8rem;color:#64748b"> / 7</span></div>'
                    f'</div>'
                    f'<div style="text-align:center">'
                    f'<div style="color:#64748b;font-size:11px">3個以上<br>的中した組</div>'
                    f'<div style="font-size:1.6rem;font-weight:700;color:#fbbf24">{total_3plus}<span style="font-size:0.8rem;color:#64748b"> / {total_combos}</span></div>'
                    f'</div>'
                    f'<div style="text-align:center">'
                    f'<div style="color:#64748b;font-size:11px">4個以上<br>的中した組</div>'
                    f'<div style="font-size:1.6rem;font-weight:700;color:#f87171">{total_4plus}<span style="font-size:0.8rem;color:#64748b"> / {total_combos}</span></div>'
                    f'</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

                for r in bt_results:
                    actual_badges = _num_badges_with_consec(r["actual"])
                    top15_set = set(r["top15"])
                    actual_set = set(r["actual"])
                    hit_nums = top15_set & actual_set
                    miss_nums = actual_set - top15_set

                    hit_str = ", ".join(f"**{n:02d}**" for n in sorted(hit_nums)) if hit_nums else "—"
                    miss_str = ", ".join(f"{n:02d}" for n in sorted(miss_nums)) if miss_nums else "—"

                    best_str = ""
                    if r["best_combo"]:
                        best_badges = _num_badges_with_consec(r["best_combo"])
                        best_str = f'最高組（{r["best_combo_hits"]}個的中）: {best_badges}'

                    # 的中数分布バー
                    dist = r.get("hit_distribution", {})
                    dist_parts = []
                    for hits_n in range(max(dist.keys()) + 1 if dist else 0):
                        cnt = dist.get(hits_n, 0)
                        if cnt > 0:
                            color = "#f87171" if hits_n >= 4 else "#fbbf24" if hits_n >= 3 else "#60a5fa" if hits_n >= 2 else "#475569"
                            dist_parts.append(f'<span style="color:{color}">{hits_n}個:{cnt}組</span>')
                    dist_html = "　".join(dist_parts) if dist_parts else ""

                    st.markdown(
                        f'<div style="border:1px solid rgba(255,255,255,0.08);border-radius:8px;padding:12px;margin:8px 0">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">'
                        f'<span style="font-weight:700;color:#e2e8f0">第{r["round"]}回</span>'
                        f'<span style="color:#60a5fa;font-weight:600">上位15中 {r["hits_top15"]}個的中</span>'
                        f'</div>'
                        f'<div style="margin-bottom:6px">実際: {actual_badges}</div>'
                        f'<div style="font-size:13px;color:#94a3b8">的中: {hit_str}　見逃し: {miss_str}</div>'
                        f'{"<div style=margin-top:6px;font-size:13px>" + best_str + "</div>" if best_str else ""}'
                        f'<div style="font-size:12px;margin-top:6px;color:#94a3b8">'
                        f'全{r["all_combos_count"]}組: 平均{r["avg_combo_hits"]}個的中　'
                        f'3個↑: {r["combos_with_3plus"]}組　4個↑: {r["combos_with_4plus"]}組</div>'
                        f'{"<div style=font-size:11px;margin-top:4px;color:#64748b>分布: " + dist_html + "</div>" if dist_html else ""}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                st.markdown(
                    '<div style="background:rgba(96,165,250,0.1);border:1px solid rgba(96,165,250,0.2);'
                    'border-radius:8px;padding:12px;margin-top:12px;font-size:13px;color:#94a3b8">'
                    '💡 <strong style="color:#60a5fa">フィードバック自動反映:</strong> '
                    'バックテストで過大予測された番号はスコアを微減、見逃した番号はスコアを微増。'
                    '次回の「おすすめの組み合わせ」に反映されます。</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.info("バックテストに十分なデータがありません。")

    # ── 予測履歴の振り返り（保存済み予測 vs 実結果）──
    _fb_analysis = analyze_prediction_accuracy(df)
    if _fb_analysis is not None:
        with st.expander("📈 保存済み予測の振り返り", expanded=False):
            _fb_text = get_feedback_summary(df)
            st.markdown(_fb_text)

    st.markdown("")

    # ── 各戦略の予測 ──
    st.markdown(
        '<div class="glass-card">'
        '<div class="section-title">🔮 戦略別の予測</div>'
        '<div class="section-subtitle">異なるアプローチでの番号選出</div>'
        "</div>",
        unsafe_allow_html=True,
    )
    for key, info in STRATEGIES.items():
        if key == "recommended":
            continue
        nums = all_results.get(key, [])
        with st.expander(f"{info['label']}"):
            st.caption(info["description"])
            if nums:
                st.markdown(_num_badges_with_consec(nums), unsafe_allow_html=True)
            else:
                st.warning("予測に失敗しました。")

# ══════════════════════════════════════════════
#  タブ2: 分析
# ══════════════════════════════════════════════
_dark_chart = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="sans-serif"),
)

# ══════════════════════════════════════════════
#  タブ2: 要因別ランキング
# ══════════════════════════════════════════════
with tab_ranking:
    st.markdown(
        '<div class="glass-card-accent">'
        '<div class="section-title">🏆 要因別ランキング</div>'
        f'<div class="section-subtitle">直近 {recent_n} 回のデータ — 9つの分析要因それぞれの上位番号</div>'
        "</div>",
        unsafe_allow_html=True,
    )

    # ── 各要因のスコアを計算 ──
    _rk_freq = get_frequency(df)
    _rk_max_freq = max(_rk_freq.values()) or 1
    _rk_recent = get_recent_activity(df, last_n=max(10, len(df) // 10))
    _rk_max_recent = max(_rk_recent.values()) or 1
    _rk_gap = get_last_appearance(df)
    _rk_max_gap = max(_rk_gap.values()) or 1
    _rk_co = get_cooccurrence_score(df)
    _rk_trend = get_trend_score(df)
    _rk_repeat = get_repeat_score(df)
    _rk_streak = get_streak_score(df)
    _rk_interval = get_interval_score(df)
    _rk_neighbor = get_neighbor_score(df)
    _rk_total = get_number_score(df)

    # 要因定義: (名前, アイコン, スコア辞書, 説明, 色)
    _factors = [
        ("総合スコア", "⭐", _rk_total, "全9要因の加重平均。最終的なおすすめ順位", "#f59e0b"),
        ("出現頻度", "🔥", {n: _rk_freq[n] / _rk_max_freq for n in ALL_NUMBERS},
         "全期間での出現回数。多いほど「出やすい番号」", "#ef4444"),
        ("直近活性度", "⚡", {n: _rk_recent[n] / _rk_max_recent for n in ALL_NUMBERS},
         "直近ウィンドウでの出現回数。最近よく出ている番号", "#f97316"),
        ("長期未出現", "💤", {n: _rk_gap[n] / _rk_max_gap for n in ALL_NUMBERS},
         "最後に出てからの経過回数。長いほど「そろそろ来る」", "#8b5cf6"),
        ("共起力", "🤝", _rk_co,
         "他の番号と一緒に出やすい度合い。ペア共起が多い番号", "#06b6d4"),
        ("トレンド", "📈", _rk_trend,
         "直近の出現率が以前より上昇している番号", "#10b981"),
        ("連続出現率", "🔄", _rk_repeat,
         "前回出た番号が次も出る傾向。前回出番号のみ対象", "#ec4899"),
        ("ストリーク", "🔥", _rk_streak,
         "連続出現の勢い。1〜3連続で上昇、4以上でペナルティ", "#f43f5e"),
        ("出現間隔周期", "⏱️", _rk_interval,
         "平均出現間隔に対して「そろそろ周期」にある番号", "#6366f1"),
        ("隣接数字効果", "🎯", _rk_neighbor,
         "前回の当選番号の±1,±2の番号。隣接ボーナス", "#14b8a6"),
    ]

    # 表示数の選択
    _rk_show_n = st.slider("表示する上位番号数", 5, 37, 10, key="rk_show_n")

    for _f_name, _f_icon, _f_scores, _f_desc, _f_color in _factors:
        _ranked = sorted(ALL_NUMBERS, key=lambda x: _f_scores[x], reverse=True)

        # ヘッダー
        st.markdown(
            f'<div class="glass-card" style="margin-top:16px;border-left:3px solid {_f_color}">'
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">'
            f'<span style="font-size:1.4rem">{_f_icon}</span>'
            f'<span style="font-size:1.1rem;font-weight:700;color:{_f_color}">{_f_name}</span>'
            f'</div>'
            f'<div style="color:#94a3b8;font-size:0.8rem;margin-bottom:12px">{_f_desc}</div>',
            unsafe_allow_html=True,
        )

        # ランキングバッジ + バー
        _rk_html = '<div style="display:flex;flex-direction:column;gap:6px">'
        _rk_top_score = _f_scores[_ranked[0]] if _f_scores[_ranked[0]] > 0 else 1
        for _ri, _rn in enumerate(_ranked[:_rk_show_n]):
            _rs = _f_scores[_rn]
            _bar_pct = (_rs / _rk_top_score * 100) if _rk_top_score > 0 else 0
            _cls = _num_class(_rn)
            _bg = {"num-r1": "#3b82f6", "num-r2": "#f97316", "num-r3": "#a855f7", "num-r4": "#22c55e"}[_cls]

            # 順位メダル
            if _ri == 0:
                _medal = '<span style="font-size:14px;margin-right:4px">🥇</span>'
            elif _ri == 1:
                _medal = '<span style="font-size:14px;margin-right:4px">🥈</span>'
            elif _ri == 2:
                _medal = '<span style="font-size:14px;margin-right:4px">🥉</span>'
            else:
                _medal = f'<span style="font-size:12px;color:#64748b;margin-right:6px;min-width:20px;display:inline-block;text-align:right">{_ri+1}</span>'

            _rk_html += (
                f'<div style="display:flex;align-items:center;gap:8px">'
                f'{_medal}'
                f'<span class="num-badge {_cls}" style="width:36px;height:36px;font-size:14px;flex-shrink:0">{_rn:02d}</span>'
                f'<div style="flex:1;background:rgba(255,255,255,0.05);border-radius:4px;height:24px;overflow:hidden">'
                f'<div style="width:{_bar_pct:.1f}%;height:100%;background:linear-gradient(90deg,{_f_color}cc,{_f_color}44);'
                f'border-radius:4px;transition:width 0.5s"></div></div>'
                f'<span style="color:#cbd5e1;font-size:12px;min-width:50px;text-align:right">{_rs:.3f}</span>'
                f'</div>'
            )

        _rk_html += '</div></div>'
        st.markdown(_rk_html, unsafe_allow_html=True)

    # ── 要因間の相関マトリックス ──
    st.markdown(
        '<div class="glass-card" style="margin-top:20px">'
        '<div class="section-title">📊 要因間の関係</div>'
        '<div style="color:#94a3b8;font-size:0.8rem;margin-bottom:12px">'
        '各要因の上位10番号がどれだけ重複しているか（共通番号数）</div>',
        unsafe_allow_html=True,
    )

    _factor_tops = {}
    for _f_name, _, _f_scores, _, _ in _factors:
        _ranked = sorted(ALL_NUMBERS, key=lambda x: _f_scores[x], reverse=True)[:10]
        _factor_tops[_f_name] = set(_ranked)

    _matrix_html = '<div style="overflow-x:auto"><table style="border-collapse:collapse;font-size:11px;width:100%">'
    _short_names = [n for n, _, _, _, _ in _factors]
    _matrix_html += '<tr><th style="padding:4px 6px;color:#64748b"></th>'
    for sn in _short_names:
        _matrix_html += f'<th style="padding:4px 3px;color:#94a3b8;font-size:9px;writing-mode:vertical-rl;text-orientation:mixed;max-width:20px">{sn}</th>'
    _matrix_html += '</tr>'

    for i, sn_i in enumerate(_short_names):
        _matrix_html += f'<tr><td style="padding:4px 6px;color:#94a3b8;font-size:10px;white-space:nowrap">{sn_i}</td>'
        for j, sn_j in enumerate(_short_names):
            overlap = len(_factor_tops[sn_i] & _factor_tops[sn_j])
            if i == j:
                _cell_bg = "rgba(255,255,255,0.1)"
                _cell_color = "#64748b"
            elif overlap >= 7:
                _cell_bg = "rgba(34,197,94,0.3)"
                _cell_color = "#22c55e"
            elif overlap >= 4:
                _cell_bg = "rgba(245,158,11,0.2)"
                _cell_color = "#f59e0b"
            else:
                _cell_bg = "rgba(255,255,255,0.03)"
                _cell_color = "#64748b"
            _matrix_html += f'<td style="padding:4px 6px;text-align:center;background:{_cell_bg};color:{_cell_color};font-weight:600">{overlap}</td>'
        _matrix_html += '</tr>'

    _matrix_html += '</table></div></div>'
    st.markdown(_matrix_html, unsafe_allow_html=True)


with tab_analysis:
    st.markdown(
        '<div class="glass-card-accent">'
        '<div class="section-title">📊 統計分析</div>'
        f'<div class="section-subtitle">直近 {recent_n} 回のデータに基づく分析結果</div>'
        "</div>",
        unsafe_allow_html=True,
    )

    # ── 頻度バーチャート ──
    freq_df = get_frequency_df(df)
    fig_freq = go.Figure(
        data=[
            go.Bar(
                x=freq_df["number"],
                y=freq_df["count"],
                marker_color=freq_df["color"],
                text=freq_df["count"],
                textposition="outside",
                hovertemplate="番号: %{x}<br>出現回数: %{y}<extra></extra>",
            )
        ]
    )
    fig_freq.update_layout(
        title=dict(text="各番号の出現頻度", font=dict(size=16)),
        xaxis_title="番号",
        yaxis_title="出現回数",
        xaxis=dict(tickmode="linear", tick0=1, dtick=1, range=[0, 38]),
        showlegend=False,
        height=380,
        margin=dict(t=50, b=40, l=50, r=20),
        **_dark_chart,
    )
    st.plotly_chart(fig_freq, use_container_width=True)
    st.caption(
        "🔴 ホット　🟠 やや多め　⬜ 平均的　🟢 やや少なめ　🔵 コールド"
    )

    st.markdown("")

    # ── ホット・コールド ──
    st.markdown(
        '<div class="section-title" style="font-size:1.1rem">🔥❄️ ホット / コールド ナンバー</div>',
        unsafe_allow_html=True,
    )
    hot, cold = get_hot_cold_numbers(df, top_n=7)
    col_h, col_c = st.columns(2)
    with col_h:
        hot_html = '<div class="glass-card"><strong style="color:#fca5a5">🔥 ホット（出現多）</strong><div style="margin-top:8px">'
        for n, cnt in hot:
            pct = cnt / len(df) * 100
            hot_html += (
                f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0">'
                f'{_num_badge(n)}'
                f'<div style="flex:1;background:#1e293b;border-radius:4px;height:8px;overflow:hidden">'
                f'<div style="width:{pct}%;height:100%;background:linear-gradient(90deg,#dc2626,#ef4444);border-radius:4px"></div></div>'
                f'<span style="color:#94a3b8;font-size:13px;min-width:40px">{cnt}回</span></div>'
            )
        hot_html += "</div></div>"
        st.markdown(hot_html, unsafe_allow_html=True)
    with col_c:
        cold_html = '<div class="glass-card"><strong style="color:#93c5fd">❄️ コールド（出現少）</strong><div style="margin-top:8px">'
        for n, cnt in cold:
            pct = cnt / len(df) * 100
            cold_html += (
                f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0">'
                f'{_num_badge(n)}'
                f'<div style="flex:1;background:#1e293b;border-radius:4px;height:8px;overflow:hidden">'
                f'<div style="width:{pct}%;height:100%;background:linear-gradient(90deg,#2563eb,#3b82f6);border-radius:4px"></div></div>'
                f'<span style="color:#94a3b8;font-size:13px;min-width:40px">{cnt}回</span></div>'
            )
        cold_html += "</div></div>"
        st.markdown(cold_html, unsafe_allow_html=True)

    st.markdown("")

    # ── 未出現経過回数 ──
    st.markdown(
        '<div class="section-title" style="font-size:1.1rem">⏱️ 未出現経過回数</div>',
        unsafe_allow_html=True,
    )
    gap = get_last_appearance(df)
    gap_df = pd.DataFrame(
        [
            {"番号": n, "経過回数": g}
            for n, g in sorted(gap.items(), key=lambda x: x[1], reverse=True)
        ]
    )
    fig_gap = px.bar(
        gap_df,
        x="番号",
        y="経過回数",
        title="番号ごとの未出現継続回数",
        color="経過回数",
        color_continuous_scale=["#3b82f6", "#f59e0b", "#ef4444"],
    )
    fig_gap.update_layout(height=350, margin=dict(t=50, b=40), showlegend=False, **_dark_chart)
    st.plotly_chart(fig_gap, use_container_width=True)

    st.markdown("")

    # ── パターン統計 ──
    st.markdown(
        '<div class="section-title" style="font-size:1.1rem">📐 パターン統計</div>',
        unsafe_allow_html=True,
    )
    stats = get_pattern_stats(df)

    col_oe, col_sum = st.columns(2)
    with col_oe:
        oe_data = stats["odd_even_distribution"]
        fig_oe = go.Figure(
            data=[
                go.Bar(
                    x=list(oe_data.keys()),
                    y=list(oe_data.values()),
                    marker=dict(
                        color=list(oe_data.values()),
                        colorscale=["#1e3a5f", "#3b82f6", "#60a5fa"],
                    ),
                )
            ]
        )
        fig_oe.update_layout(
            title=dict(text="奇数の個数分布（7個中）", font=dict(size=14)),
            xaxis_title="奇数の個数",
            yaxis_title="回数",
            xaxis=dict(tickmode="linear"),
            height=300,
            **_dark_chart,
        )
        st.plotly_chart(fig_oe, use_container_width=True)

    with col_sum:
        sums = stats["sum_distribution"]
        fig_sum = go.Figure(
            data=[go.Histogram(x=sums, nbinsx=25, marker_color="#3b82f6")]
        )
        fig_sum.update_layout(
            title=dict(text="7数字の合計値分布", font=dict(size=14)),
            xaxis_title="合計値",
            yaxis_title="回数",
            height=300,
            **_dark_chart,
        )
        st.plotly_chart(fig_sum, use_container_width=True)

    col_hl, col_co = st.columns(2)
    with col_hl:
        hl_data = stats["high_low_distribution"]
        fig_hl = go.Figure(
            data=[
                go.Bar(
                    x=list(hl_data.keys()),
                    y=list(hl_data.values()),
                    marker=dict(
                        color=list(hl_data.values()),
                        colorscale=["#713f12", "#f59e0b", "#fbbf24"],
                    ),
                )
            ]
        )
        fig_hl.update_layout(
            title=dict(text="高数字（19以上）の個数分布", font=dict(size=14)),
            xaxis_title="高数字の個数",
            yaxis_title="回数",
            xaxis=dict(tickmode="linear"),
            height=300,
            **_dark_chart,
        )
        st.plotly_chart(fig_hl, use_container_width=True)

    with col_co:
        consec = stats["consecutive_counts"]
        consec_cnt = pd.Series(consec).value_counts().sort_index()
        fig_co = go.Figure(
            data=[
                go.Bar(
                    x=consec_cnt.index.tolist(),
                    y=consec_cnt.values.tolist(),
                    marker=dict(
                        color=consec_cnt.values.tolist(),
                        colorscale=["#14532d", "#22c55e", "#86efac"],
                    ),
                )
            ]
        )
        fig_co.update_layout(
            title=dict(text="連続数字ペアの数分布", font=dict(size=14)),
            xaxis_title="連続ペアの数",
            yaxis_title="回数",
            xaxis=dict(tickmode="linear"),
            height=300,
            **_dark_chart,
        )
        st.plotly_chart(fig_co, use_container_width=True)

    st.markdown("")

    # ── 共起分析 ──
    st.markdown(
        '<div class="section-title" style="font-size:1.1rem">🔗 共起分析（一緒に出やすいペア）</div>',
        unsafe_allow_html=True,
    )
    top_pairs = get_top_pairs(df, top_n=15)
    if top_pairs:
        pair_html = '<div class="glass-card"><div style="display:flex;flex-wrap:wrap;gap:6px">'
        max_cnt = top_pairs[0][2] if top_pairs else 1
        for a, b, cnt in top_pairs:
            intensity = cnt / max_cnt
            opacity = 0.3 + intensity * 0.7
            pair_html += (
                f'<div style="display:flex;align-items:center;gap:4px;'
                f'background:rgba(96,165,250,{opacity:.2f});border:1px solid rgba(96,165,250,{opacity:.1f});'
                f'border-radius:10px;padding:6px 12px">'
                f'{_num_badge(a)}{_num_badge(b)}'
                f'<span style="color:#94a3b8;font-size:13px;margin-left:4px">{cnt}回</span>'
                f'</div>'
            )
        pair_html += '</div></div>'
        st.markdown(pair_html, unsafe_allow_html=True)
        st.caption("色の濃さが共起回数の多さを表します。よく一緒に出る番号ペアほど濃い色です。")

    st.markdown("")

    # ── トレンド分析 ──
    st.markdown(
        '<div class="section-title" style="font-size:1.1rem">📈 トレンド分析（上昇傾向の番号）</div>',
        unsafe_allow_html=True,
    )
    trending = get_trending_numbers(df, top_n=10)
    if trending:
        col_up, col_down = st.columns(2)
        with col_up:
            up_html = '<div class="glass-card"><strong style="color:#86efac">📈 上昇トレンド</strong><div style="margin-top:8px">'
            for n, change in trending:
                if change <= 0:
                    continue
                bar_w = min(change * 500, 100)
                up_html += (
                    f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0">'
                    f'{_num_badge(n)}'
                    f'<div style="flex:1;background:#1e293b;border-radius:4px;height:8px;overflow:hidden">'
                    f'<div style="width:{bar_w}%;height:100%;background:linear-gradient(90deg,#22c55e,#4ade80);border-radius:4px"></div></div>'
                    f'<span style="color:#86efac;font-size:13px;min-width:50px">+{change:.3f}</span></div>'
                )
            up_html += '</div></div>'
            st.markdown(up_html, unsafe_allow_html=True)

        with col_down:
            # 下降トレンド（trending の逆）
            declining = get_trending_numbers(df, top_n=37)
            declining_bottom = [(n, c) for n, c in reversed(declining) if c < 0][:10]
            down_html = '<div class="glass-card"><strong style="color:#fca5a5">📉 下降トレンド</strong><div style="margin-top:8px">'
            for n, change in declining_bottom:
                bar_w = min(abs(change) * 500, 100)
                down_html += (
                    f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0">'
                    f'{_num_badge(n)}'
                    f'<div style="flex:1;background:#1e293b;border-radius:4px;height:8px;overflow:hidden">'
                    f'<div style="width:{bar_w}%;height:100%;background:linear-gradient(90deg,#ef4444,#f87171);border-radius:4px"></div></div>'
                    f'<span style="color:#fca5a5;font-size:13px;min-width:50px">{change:.3f}</span></div>'
                )
            down_html += '</div></div>'
            st.markdown(down_html, unsafe_allow_html=True)

        st.caption("直近の出現率を少し前の期間と比較し、変化量を表示。上昇中の番号は勢いがあり、次回も出やすい傾向。")

    st.markdown("")

    # ── 連続出現分析 ──
    st.markdown(
        '<div class="section-title" style="font-size:1.1rem">🔁 連続出現分析（前回→次回の引き継ぎ）</div>',
        unsafe_allow_html=True,
    )
    repeat_stats = get_repeat_stats(df)

    col_rep1, col_rep2 = st.columns(2)
    with col_rep1:
        # 分布グラフ
        rep_dist = repeat_stats["repeat_distribution"]
        fig_rep = go.Figure(
            data=[
                go.Bar(
                    x=list(rep_dist.keys()),
                    y=list(rep_dist.values()),
                    marker=dict(
                        color=list(rep_dist.values()),
                        colorscale=["#1e3a5f", "#3b82f6", "#60a5fa"],
                    ),
                    text=list(rep_dist.values()),
                    textposition="outside",
                )
            ]
        )
        fig_rep.update_layout(
            title=dict(text="前回からの引き継ぎ個数分布", font=dict(size=14)),
            xaxis_title="引き継ぎ個数（7個中）",
            yaxis_title="回数",
            xaxis=dict(tickmode="linear"),
            height=300,
            **_dark_chart,
        )
        st.plotly_chart(fig_rep, use_container_width=True)

    with col_rep2:
        avg = repeat_stats["avg_repeats"]
        st.markdown(
            f'<div class="glass-card">'
            f'<div style="text-align:center">'
            f'<div style="color:#64748b;font-size:13px;margin-bottom:4px">平均引き継ぎ個数</div>'
            f'<div style="font-size:3rem;font-weight:800;color:#60a5fa">{avg:.1f}</div>'
            f'<div style="color:#64748b;font-size:13px;margin-top:4px">/ 7 個中</div>'
            f'</div>'
            f'<div style="margin-top:16px;color:#94a3b8;font-size:13px;line-height:1.8">'
            f'前回の7個のうち平均 <b style="color:#60a5fa">{avg:.1f}個</b> が次の回でも出現。<br>'
            f'つまり前回の番号は次回にも <b style="color:#60a5fa">{avg/7*100:.0f}%</b> の確率で引き継がれます。'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        # 前回の番号で連続出現率が高いもの
        per_num = repeat_stats["per_number_repeat_rate"]
        last_draw = sorted(int(n) for n in get_main_numbers(df)[-1])
        st.markdown(
            '<div style="margin-top:12px;color:#94a3b8;font-size:13px"><b>前回の番号の連続出現率:</b></div>',
            unsafe_allow_html=True,
        )
        rate_html = '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:6px">'
        for n in last_draw:
            rate = per_num.get(n, 0)
            rate_html += (
                f'{_num_badge(n)}'
                f'<span style="color:#94a3b8;font-size:12px;margin-right:8px">{rate*100:.0f}%</span>'
            )
        rate_html += '</div>'
        st.markdown(rate_html, unsafe_allow_html=True)

    st.caption("前回の当選番号が次の回でも出る確率を分析。連続出現率が高い番号はスコアに加算されます。")

    st.markdown("")

    # ── 出現間隔の周期性 ──
    st.markdown(
        '<div class="section-title" style="font-size:1.1rem">⏰ 出現間隔の周期性（そろそろ来る番号）</div>',
        unsafe_allow_html=True,
    )
    interval_data = get_interval_stats(df)
    # 周期比率（current_gap / avg_interval）が1.0に近いor超えた番号 = そろそろ出る
    due_numbers = sorted(
        [(n, d) for n, d in interval_data.items() if d["avg_interval"] > 0],
        key=lambda x: x[1]["cycle_ratio"],
        reverse=True,
    )[:12]

    due_html = '<div class="glass-card"><div style="display:flex;flex-wrap:wrap;gap:8px">'
    for n, d in due_numbers:
        ratio = d["cycle_ratio"]
        if ratio >= 1.0:
            border_color = "#ef4444"
            label = "周期超過"
        elif ratio >= 0.8:
            border_color = "#f59e0b"
            label = "まもなく"
        else:
            border_color = "#3b82f6"
            label = f"{ratio:.0%}"
        due_html += (
            f'<div style="display:flex;flex-direction:column;align-items:center;'
            f'border:2px solid {border_color};border-radius:12px;padding:8px 10px;min-width:70px">'
            f'{_num_badge(n)}'
            f'<span style="color:#94a3b8;font-size:11px;margin-top:4px">'
            f'平均{d["avg_interval"]:.0f}回おき</span>'
            f'<span style="color:#94a3b8;font-size:11px">現在{d["current_gap"]}回未出現</span>'
            f'<span style="color:{border_color};font-size:12px;font-weight:700">{label}</span>'
            f'</div>'
        )
    due_html += '</div></div>'
    st.markdown(due_html, unsafe_allow_html=True)
    st.caption("各番号の平均出現間隔に対して、現在の未出現回数がどれだけ近いかを表示。「周期超過」は平均間隔を超えて出ていない番号。")

    st.markdown("")

    # ── 隣接数字効果 ──
    st.markdown(
        '<div class="section-title" style="font-size:1.1rem">🎯 隣接数字効果（前回の±1, ±2）</div>',
        unsafe_allow_html=True,
    )
    neighbor_nums = get_neighbor_numbers(df)
    last_draw_display = sorted(int(n) for n in get_main_numbers(df)[-1])

    st.markdown(
        f'<div class="glass-card">'
        f'<div style="margin-bottom:8px;color:#94a3b8;font-size:13px">'
        f'前回の番号: {" ".join(_num_badge(n) for n in last_draw_display)} の隣接番号</div>'
        f'<div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center">',
        unsafe_allow_html=True,
    )
    if neighbor_nums:
        neigh_html = '<div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center">'
        for n, score in neighbor_nums:
            intensity = score
            neigh_html += (
                f'<div style="display:flex;align-items:center;gap:4px;'
                f'background:rgba(250,204,21,{0.1 + intensity * 0.2});'
                f'border:1px solid rgba(250,204,21,{0.2 + intensity * 0.3});'
                f'border-radius:10px;padding:4px 8px">'
                f'{_num_badge(n)}'
                f'<span style="color:#fde68a;font-size:12px;font-weight:600">{score:.0%}</span>'
                f'</div>'
            )
        neigh_html += '</div>'
        st.markdown(neigh_html, unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)
    st.caption("前回の番号の±1, ±2の数字は統計的に次回やや出やすい傾向があります。スコアの高い番号ほど複数の前回番号に隣接しています。")

# ══════════════════════════════════════════════
#  タブ3: 過去の結果
# ══════════════════════════════════════════════
with tab_history:
    st.markdown(
        '<div class="glass-card-accent">'
        '<div class="section-title">📋 過去の抽選結果</div>'
        f'<div class="section-subtitle">全 {len(df_raw)} 回分のデータ</div>'
        "</div>",
        unsafe_allow_html=True,
    )

    hist_view = st.radio(
        "表示形式",
        ["出目表", "一覧表"],
        horizontal=True,
    )

    if hist_view == "出目表":
        # ── 出目表（回号 × 番号のヒートマップ） ──
        st.caption("● が出た番号。色は番号の範囲を表します。")

        deme_n = st.slider("表示する直近の回数", 10, len(df_raw), min(50, len(df_raw)), 1, key="deme_n")
        deme_df = df_raw.tail(deme_n).sort_values("round", ascending=False)

        # 各回の出目セットを作成
        deme_rows = []
        for _, r in deme_df.iterrows():
            nums = set(int(r[f"n{i}"]) for i in range(1, 8))
            deme_rows.append((int(r["round"]), nums))

        # HTML テーブル生成
        # 色設定
        _deme_colors = {
            "num-r1": "#2563eb",
            "num-r2": "#16a34a",
            "num-r3": "#ea580c",
            "num-r4": "#9333ea",
        }

        html = (
            '<div style="overflow-x:auto">'
            '<table style="border-collapse:collapse;font-size:12px;width:100%">'
            '<thead><tr>'
            '<th style="position:sticky;left:0;z-index:2;background:#0f172a;padding:4px 6px;'
            'border-bottom:2px solid #334155;color:#64748b;min-width:50px">回</th>'
        )
        for n in ALL_NUMBERS:
            cls = _num_class(n)
            bg = _deme_colors[cls]
            html += (
                f'<th style="padding:2px;border-bottom:2px solid #334155;min-width:24px;'
                f'text-align:center;color:{bg};font-weight:700;font-size:11px">{n}</th>'
            )
        html += '</tr></thead><tbody>'

        for round_no, nums in deme_rows:
            html += f'<tr><td style="position:sticky;left:0;z-index:1;background:#0f172a;padding:3px 6px;border-bottom:1px solid #1e293b;color:#94a3b8;font-weight:600;font-size:12px">{round_no}</td>'
            for n in ALL_NUMBERS:
                if n in nums:
                    cls = _num_class(n)
                    c = _deme_colors[cls]
                    html += (
                        f'<td style="text-align:center;padding:2px;border-bottom:1px solid #1e293b">'
                        f'<span style="display:inline-block;width:18px;height:18px;border-radius:50%;'
                        f'background:{c};box-shadow:0 0 6px {c}60"></span></td>'
                    )
                else:
                    html += '<td style="text-align:center;padding:2px;border-bottom:1px solid #1e293b;color:#1e293b">·</td>'
            html += '</tr>'

        html += '</tbody></table></div>'
        st.markdown(html, unsafe_allow_html=True)

    else:
        # ── 従来の一覧表 ──
        display_df = (
            df_raw.copy().sort_values("round", ascending=False).reset_index(drop=True)
        )
        rename = {
            "round": "回号",
            "date": "抽選日",
            "n1": "第1", "n2": "第2", "n3": "第3",
            "n4": "第4", "n5": "第5", "n6": "第6", "n7": "第7",
            "b1": "ボーナス1", "b2": "ボーナス2",
        }
        show_cols = [c for c in rename if c in display_df.columns]
        display_df = display_df[show_cols].rename(columns=rename)

        st.dataframe(display_df, use_container_width=True, hide_index=True, height=500)

# ══════════════════════════════════════════════
#  タブ5: 模擬抽選シミュレーション
# ══════════════════════════════════════════════
with tab_sim:
    import random as _sim_random
    import time as _sim_time

    st.markdown(
        '<div class="glass-card">'
        '<div class="section-title">🎰 模擬抽選シミュレーション</div>'
        '<div class="section-subtitle">'
        'おすすめの組み合わせ vs ランダム7組で仮想抽選！当たるのはどっち？'
        '</div></div>',
        unsafe_allow_html=True,
    )

    # 手持ちのおすすめ組
    _sim_combos = combos[:10] if combos else []

    st.markdown("")

    # おすすめから選ぶ数
    _sim_col1, _sim_col2 = st.columns(2)
    with _sim_col1:
        _sim_rec_count = st.number_input(
            "おすすめから何組使う？", min_value=1, max_value=min(10, len(_sim_combos)) if _sim_combos else 1,
            value=min(5, len(_sim_combos)) if _sim_combos else 1, step=1, key="sim_rec_n",
        )
    with _sim_col2:
        _sim_rnd_count = st.number_input(
            "ランダム何組と勝負？", min_value=1, max_value=20, value=5, step=1, key="sim_rnd_n",
        )

    # おすすめ組を表示
    st.markdown("**🎯 おすすめチーム**")
    _sim_rec_picks = _sim_combos[:_sim_rec_count] if _sim_combos else []
    for i, c in enumerate(_sim_rec_picks, 1):
        badges = _num_badges_with_consec(sorted(c))
        st.markdown(
            f'<div style="margin:4px 0;display:flex;align-items:center;gap:8px">'
            f'<span style="color:#60a5fa;font-weight:700;min-width:30px">#{i}</span>{badges}</div>',
            unsafe_allow_html=True,
        )

    # ランダム組を生成
    if "sim_random_picks" not in st.session_state or st.session_state.get("_sim_rnd_n_cache") != _sim_rnd_count:
        st.session_state["sim_random_picks"] = [
            sorted(_sim_random.sample(range(1, 38), 7)) for _ in range(_sim_rnd_count)
        ]
        st.session_state["_sim_rnd_n_cache"] = _sim_rnd_count

    _sim_rnd_picks = st.session_state["sim_random_picks"]

    st.markdown("**🎲 ランダムチーム**")
    for i, c in enumerate(_sim_rnd_picks, 1):
        badges = _num_badges_with_consec(c)
        st.markdown(
            f'<div style="margin:4px 0;display:flex;align-items:center;gap:8px">'
            f'<span style="color:#a78bfa;font-weight:700;min-width:30px">#{i}</span>{badges}</div>',
            unsafe_allow_html=True,
        )

    if st.button("🔀 ランダムチームを入れ替え", key="sim_reshuffle"):
        st.session_state["sim_random_picks"] = [
            sorted(_sim_random.sample(range(1, 38), 7)) for _ in range(_sim_rnd_count)
        ]
        st.rerun()

    st.markdown("")
    st.markdown("---")

    # 抽選実行
    _sim_col_btn, _sim_col_count = st.columns([1, 1])
    with _sim_col_count:
        _sim_trials = st.selectbox("抽選回数", [1, 10, 100, 1000], index=0, key="sim_trials")

    with _sim_col_btn:
        _sim_run = st.button("🎰 抽選スタート！", type="primary", use_container_width=True, key="sim_start")

    if _sim_run:
        rec_wins = 0
        rnd_wins = 0
        draws = 0
        rec_total_hits = 0
        rnd_total_hits = 0
        rec_best_ever = 0
        rnd_best_ever = 0
        rec_3plus = 0
        rnd_3plus = 0

        _sim_placeholder = st.empty()

        for trial in range(_sim_trials):
            # 仮想抽選: 1-37から7個ランダム
            winning = sorted(_sim_random.sample(range(1, 38), 7))
            winning_set = set(winning)

            # おすすめチームの最高的中
            rec_best = 0
            for c in _sim_rec_picks:
                h = len(set(c) & winning_set)
                rec_best = max(rec_best, h)
            rec_total_hits += rec_best
            rec_best_ever = max(rec_best_ever, rec_best)
            if rec_best >= 3:
                rec_3plus += 1

            # ランダムチームの最高的中
            rnd_best = 0
            for c in _sim_rnd_picks:
                h = len(set(c) & winning_set)
                rnd_best = max(rnd_best, h)
            rnd_total_hits += rnd_best
            rnd_best_ever = max(rnd_best_ever, rnd_best)
            if rnd_best >= 3:
                rnd_3plus += 1

            if rec_best > rnd_best:
                rec_wins += 1
            elif rnd_best > rec_best:
                rnd_wins += 1
            else:
                draws += 1

        # 結果表示
        total = _sim_trials
        last_winning = winning  # 最後の抽選結果

        # 1回だけの場合は演出付き
        if _sim_trials == 1:
            st.markdown(
                '<div class="glass-card" style="text-align:center">'
                '<div style="color:#64748b;font-size:13px;margin-bottom:8px">抽選結果</div>'
                '</div>',
                unsafe_allow_html=True,
            )
            win_badges = _num_badges_with_consec(last_winning)
            st.markdown(
                f'<div style="text-align:center;margin:16px 0">{win_badges}</div>',
                unsafe_allow_html=True,
            )

            st.markdown("")

            # おすすめチームの結果
            st.markdown("**🎯 おすすめチーム結果**")
            for i, c in enumerate(_sim_rec_picks, 1):
                hits = len(set(c) & set(last_winning))
                hit_nums = set(c) & set(last_winning)
                badges_html = ""
                for n in sorted(c):
                    cls = _num_class(n)
                    if n in hit_nums:
                        badges_html += (
                            f'<span class="num-badge {cls}" '
                            f'style="box-shadow:0 0 12px rgba(251,191,36,0.6);border:2px solid #fbbf24">'
                            f'{n:02d}</span>'
                        )
                    else:
                        badges_html += (
                            f'<span class="num-badge {cls}" style="opacity:0.4">{n:02d}</span>'
                        )
                color = "#fbbf24" if hits >= 3 else "#60a5fa" if hits >= 2 else "#94a3b8"
                st.markdown(
                    f'<div style="margin:4px 0;display:flex;align-items:center;gap:8px">'
                    f'<span style="color:#60a5fa;font-weight:700;min-width:30px">#{i}</span>'
                    f'{badges_html}'
                    f'<span style="color:{color};font-weight:700;margin-left:8px">{hits}個的中</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            st.markdown("**🎲 ランダムチーム結果**")
            for i, c in enumerate(_sim_rnd_picks, 1):
                hits = len(set(c) & set(last_winning))
                hit_nums = set(c) & set(last_winning)
                badges_html = ""
                for n in sorted(c):
                    cls = _num_class(n)
                    if n in hit_nums:
                        badges_html += (
                            f'<span class="num-badge {cls}" '
                            f'style="box-shadow:0 0 12px rgba(251,191,36,0.6);border:2px solid #fbbf24">'
                            f'{n:02d}</span>'
                        )
                    else:
                        badges_html += (
                            f'<span class="num-badge {cls}" style="opacity:0.4">{n:02d}</span>'
                        )
                color = "#fbbf24" if hits >= 3 else "#a78bfa" if hits >= 2 else "#94a3b8"
                st.markdown(
                    f'<div style="margin:4px 0;display:flex;align-items:center;gap:8px">'
                    f'<span style="color:#a78bfa;font-weight:700;min-width:30px">#{i}</span>'
                    f'{badges_html}'
                    f'<span style="color:{color};font-weight:700;margin-left:8px">{hits}個的中</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        # 勝敗サマリー
        rec_avg = rec_total_hits / total if total > 0 else 0
        rnd_avg = rnd_total_hits / total if total > 0 else 0

        if rec_wins > rnd_wins:
            winner_text = "🎯 おすすめチームの勝ち！"
            winner_color = "#60a5fa"
        elif rnd_wins > rec_wins:
            winner_text = "🎲 ランダムチームの勝ち！"
            winner_color = "#a78bfa"
        else:
            winner_text = "🤝 引き分け！"
            winner_color = "#94a3b8"

        st.markdown(
            f'<div class="glass-card" style="text-align:center;margin-top:16px">'
            f'<div style="font-size:1.5rem;font-weight:800;color:{winner_color};margin-bottom:12px">'
            f'{winner_text}</div>'
            f'<div style="display:flex;justify-content:center;gap:32px;flex-wrap:wrap">'
            # おすすめ
            f'<div style="text-align:center;min-width:140px">'
            f'<div style="color:#60a5fa;font-weight:700;margin-bottom:4px">🎯 おすすめ</div>'
            f'<div style="font-size:1.8rem;font-weight:800;color:#60a5fa">{rec_wins}</div>'
            f'<div style="color:#64748b;font-size:12px">勝ち</div>'
            f'<div style="color:#94a3b8;font-size:12px;margin-top:4px">'
            f'平均{rec_avg:.2f}個 / 最高{rec_best_ever}個 / 3個↑:{rec_3plus}回</div>'
            f'</div>'
            # 引き分け
            f'<div style="text-align:center;min-width:60px">'
            f'<div style="color:#64748b;font-weight:700;margin-bottom:4px">🤝</div>'
            f'<div style="font-size:1.8rem;font-weight:800;color:#64748b">{draws}</div>'
            f'<div style="color:#64748b;font-size:12px">引分</div>'
            f'</div>'
            # ランダム
            f'<div style="text-align:center;min-width:140px">'
            f'<div style="color:#a78bfa;font-weight:700;margin-bottom:4px">🎲 ランダム</div>'
            f'<div style="font-size:1.8rem;font-weight:800;color:#a78bfa">{rnd_wins}</div>'
            f'<div style="color:#64748b;font-size:12px">勝ち</div>'
            f'<div style="color:#94a3b8;font-size:12px;margin-top:4px">'
            f'平均{rnd_avg:.2f}個 / 最高{rnd_best_ever}個 / 3個↑:{rnd_3plus}回</div>'
            f'</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        if _sim_trials >= 10:
            st.caption(
                f"※ {_sim_trials}回の仮想抽選でおすすめ{_sim_rec_count}組 vs ランダム{_sim_rnd_count}組を対戦。"
                f"各回で最高的中数が多い方が勝ち。"
            )


# ══════════════════════════════════════════════
#  タブ6: AI相談
# ══════════════════════════════════════════════
with tab_ai:
    st.markdown(
        '<div class="glass-card-accent">'
        '<div class="section-title">🤖 AI に相談（Claude Web 連携）</div>'
        '<div class="section-subtitle">分析データを自動でまとめて Claude に質問できます</div>'
        "</div>",
        unsafe_allow_html=True,
    )

    # ── 分析サマリーを自動生成 ──
    _scores_ai = get_number_score(df)
    _top15 = sorted(ALL_NUMBERS, key=lambda x: _scores_ai[x], reverse=True)[:15]
    _hot_ai, _cold_ai = get_hot_cold_numbers(df, top_n=7)
    _repeat_ai = get_repeat_stats(df)
    _trending_up_ai = get_trending_numbers(df, top_n=7)
    _trending_all = get_trending_numbers(df, top_n=37)
    _trending_down_ai = [(n, c) for n, c in reversed(_trending_all) if c < 0][:7]
    _last_nums_ai = sorted(int(n) for n in get_main_numbers(df)[-1])
    _top_pairs_ai = get_top_pairs(df, top_n=10)
    _gap_ai = get_last_appearance(df)
    _long_absent = sorted(_gap_ai.items(), key=lambda x: x[1], reverse=True)[:7]
    _per_num_rr = _repeat_ai["per_number_repeat_rate"]
    _streak_ai = get_streak_stats(df)
    _recent_draws_text = get_recent_draws_text(df_raw, last_n=30)
    _interval_ai = get_interval_stats(df)
    _neighbor_ai = get_neighbor_numbers(df)

    # 全番号の出現回数
    from modules.analysis import get_frequency
    _freq_all = get_frequency(df)

    # 現在連続出現中の番号
    _active_streaks = sorted(
        [(n, s["current_streak"]) for n, s in _streak_ai.items() if s["current_streak"] > 0],
        key=lambda x: x[1], reverse=True,
    )
    # 過去最大ストリーク上位
    _max_streaks = sorted(
        [(n, s["max_streak"]) for n, s in _streak_ai.items()],
        key=lambda x: x[1], reverse=True,
    )[:10]

    _analysis_summary = f"""# ロト7 統計分析レポート（自動生成）

## 基本情報
- 分析対象: 直近 {recent_n} 回（全 {len(df_raw)} 回中）
- 次回: 第 {next_round} 回
- 前回（第{next_round - 1}回）の当選番号: {', '.join(f'{n:02d}' for n in _last_nums_ai)}

## 全番号の出現回数（全{recent_n}回中）
{', '.join(f'{n:02d}:{_freq_all[n]}回' for n in ALL_NUMBERS)}

## 総合スコア上位15番号（9要因: 頻度14%+活性度10%+未出現8%+共起13%+トレンド15%+連続出現11%+ストリーク10%+周期性10%+隣接効果9%）
{chr(10).join(f'  {i+1}位: {n:02d} (スコア {_scores_ai[n]:.3f})' for i, n in enumerate(_top15))}

## ホット番号（出現回数上位）
{', '.join(f'{n:02d}({c}回)' for n, c in _hot_ai)}

## コールド番号（出現回数下位）
{', '.join(f'{n:02d}({c}回)' for n, c in _cold_ai)}

## 長期未出現番号（経過回数が多い順）
{', '.join(f'{n:02d}({g}回未出現)' for n, g in _long_absent)}

## 各番号の未出現経過回数（全番号）
{', '.join(f'{n:02d}:{_gap_ai[n]}回' for n in ALL_NUMBERS)}

## 上昇トレンド（直近で出現率が上昇中）
{', '.join(f'{n:02d}(+{ch:.4f})' for n, ch in _trending_up_ai)}

## 下降トレンド（直近で出現率が下降中）
{', '.join(f'{n:02d}({ch:.4f})' for n, ch in _trending_down_ai)}

## 共起ペア（よく一緒に出る番号TOP10）
{', '.join(f'{a:02d}-{b:02d}({c}回)' for a, b, c in _top_pairs_ai)}

## 連続出現分析（前回→次回の引き継ぎ）
- 平均引き継ぎ個数: {_repeat_ai['avg_repeats']:.1f} / 7個 ({_repeat_ai['avg_repeats']/7*100:.0f}%)
- 引き継ぎ個数分布: {_repeat_ai['repeat_distribution']}
- 前回の番号ごとの連続出現率:
{chr(10).join(f'  {n:02d}: {_per_num_rr.get(n, 0)*100:.1f}%' for n in _last_nums_ai)}

## 連続出現ストリーク（各番号が何回連続で出ているか）
### 現在連続出現中の番号（最新回から遡って）
{chr(10).join(f'  {n:02d}: 現在{s}連続出現中' for n, s in _active_streaks) if _active_streaks else '  なし'}

### 各番号の現在の連続出現数と過去最大連続出現数（全37番号）
{chr(10).join(f'  {n:02d}: 現在{_streak_ai[n]["current_streak"]}連続 / 過去最大{_streak_ai[n]["max_streak"]}連続' for n in ALL_NUMBERS)}

## 出現間隔の周期性（各番号の平均出現間隔と現在の未出現回数）
{chr(10).join(f'  {n:02d}: 平均{d["avg_interval"]}回おき / 現在{d["current_gap"]}回未出現 / 周期比率{d["cycle_ratio"]}' for n, d in sorted(_interval_ai.items()) if d["avg_interval"] > 0)}

## 隣接数字効果（前回の番号±1,±2で次回出やすい番号）
前回の番号: {', '.join(f'{n:02d}' for n in _last_nums_ai)}
隣接効果の高い番号: {', '.join(f'{n:02d}(スコア{s:.0%})' for n, s in _neighbor_ai[:10])}

## 直近30回の当選番号（実データ）
{_recent_draws_text}

## このデータに基づいて質問に答えてください。
- 具体的な番号を挙げて根拠を示してください
- ロト7は完全ランダム抽選である前提で、統計的傾向として話してください
- 各番号の連続出現ストリーク情報を活用し、「何連続で出ているか」「過去に何連続まであったか」などの質問に正確に答えてください
- 出現間隔の周期性を活用し、「そろそろ出る番号」の質問には周期比率が1.0以上の番号を挙げてください
- 隣接数字効果を活用し、前回の番号の近くの数字についても言及してください
"""

    # ── サマリー表示 ──
    with st.expander("📊 AI に送る分析データ（自動生成）", expanded=False):
        st.code(_analysis_summary, language="markdown")

    st.markdown("---")

    # ── クイック質問テンプレート ──
    st.markdown(
        '<div class="section-title" style="font-size:1.1rem">💬 質問を作成</div>',
        unsafe_allow_html=True,
    )

    quick_templates = [
        "次回の第{next}回で出やすい番号トップ7とその根拠を教えて",
        "前回の番号 {last} の中で次回も出そうなものはどれ？",
        "今の分析で見落としている視点やリスクはある？",
        "ホット番号とコールド番号のどちらを重視すべき？",
        "おすすめの7個の組み合わせを3パターン提案して",
        "連続出現率が高い番号を中心にした戦略を考えて",
    ]

    st.markdown("**クイック質問（クリックで入力欄にセット）:**")
    qcols = st.columns(2)
    selected_quick = None
    for i, tmpl in enumerate(quick_templates):
        q_text = tmpl.format(next=next_round, last=", ".join(f"{n:02d}" for n in _last_nums_ai))
        with qcols[i % 2]:
            if st.button(f"📝 {q_text[:40]}...", key=f"qt_{i}", use_container_width=True):
                selected_quick = q_text

    st.markdown("")

    # ── 質問入力 ──
    default_q = selected_quick or ""
    user_question = st.text_area(
        "質問を入力",
        value=default_q,
        height=100,
        placeholder="例: 次回出やすい番号を根拠付きで教えて",
        key="ai_question",
    )

    # ── コピー用テキスト生成 ──
    full_prompt = _analysis_summary + "\n---\n\n## 質問\n" + (user_question or "次回出やすい番号を分析データに基づいて教えてください")

    st.markdown("---")

    st.markdown(
        '<div class="section-title" style="font-size:1.1rem">🚀 Claude に送る</div>',
        unsafe_allow_html=True,
    )
    st.caption("下のボタンで分析データ + 質問をコピーし、Claude を開いて貼り付けてください。")

    col_copy, col_open = st.columns(2)

    with col_copy:
        st.code(full_prompt, language="markdown")
        st.markdown(
            f"""
            <button onclick="navigator.clipboard.writeText(document.querySelector('#copy-target').textContent).then(()=>alert('コピーしました！'))"
                style="display:none">Copy</button>
            """,
            unsafe_allow_html=True,
        )
        # Streamlit ネイティブのコピー方法: st.code の中身はユーザーが選択コピーできるが、
        # ボタン1つでコピーするには st.components.v1.html を使う
        import streamlit.components.v1 as components
        _escaped = full_prompt.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
        components.html(
            f"""
            <button id="copyBtn" style="
                background:linear-gradient(135deg,#2563eb,#3b82f6);
                color:white; border:none; border-radius:8px;
                padding:10px 20px; font-size:15px; font-weight:700;
                cursor:pointer; width:100%;
                box-shadow:0 2px 8px rgba(37,99,235,0.3);
            ">📋 分析+質問をコピー</button>
            <script>
            document.getElementById('copyBtn').addEventListener('click', function() {{
                const text = `{_escaped}`;
                navigator.clipboard.writeText(text).then(() => {{
                    this.textContent = '✅ コピーしました！';
                    this.style.background = 'linear-gradient(135deg,#15803d,#22c55e)';
                    setTimeout(() => {{
                        this.textContent = '📋 分析+質問をコピー';
                        this.style.background = 'linear-gradient(135deg,#2563eb,#3b82f6)';
                    }}, 2000);
                }});
            }});
            </script>
            """,
            height=50,
        )

    with col_open:
        st.markdown("")
        st.markdown("")
        st.link_button(
            "🌐 Claude を開く (claude.ai)",
            "https://claude.ai/new",
            use_container_width=True,
            type="primary",
        )
        st.caption("開いたら、チャット欄に貼り付け (Ctrl+V) して送信してください。")

    # ── 使い方ガイド ──
    with st.expander("📖 Claude Web 版の使い方", expanded=False):
        st.markdown(
            "1. 上の「クイック質問」を選ぶか、自分で質問を入力\n"
            "2. **📋 分析+質問をコピー** ボタンをクリック\n"
            "3. **🌐 Claude を開く** ボタンで claude.ai を開く\n"
            "4. チャット欄に **Ctrl+V** で貼り付けて送信\n"
        )

    # ══════════════════════════════════════════
    #  Gemini AI チャット（API）
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown(
        '<div class="glass-card">'
        '<div class="section-title">💬 Gemini AI チャット</div>'
        '<div class="section-subtitle">サイドバーで API Key を入力するとアプリ内で直接 AI に質問できます</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    _gemini_key = st.session_state.get("gemini_key", "")

    if not _gemini_key:
        st.info(
            "サイドバーで **Gemini API Key** を入力するとチャットが使えます。\n\n"
            "[Google AI Studio](https://aistudio.google.com/apikey) で無料で取得できます。"
        )
    else:
        # チャット履歴
        if "gemini_messages" not in st.session_state:
            st.session_state["gemini_messages"] = []

        # クイック質問
        gcols = st.columns(3)
        _gquick = [
            "次回の注目番号は？",
            "前回の番号は次も出る？",
            "おすすめ組み合わせを3つ提案して",
        ]
        g_quick_q = None
        for i, q in enumerate(_gquick):
            with gcols[i]:
                if st.button(q, key=f"gq_{i}", use_container_width=True):
                    g_quick_q = q

        # 履歴表示
        for msg in st.session_state["gemini_messages"]:
            if msg["role"] == "user":
                st.markdown(
                    f'<div style="background:#1e3a5f;border:1px solid #2563eb;border-radius:12px;'
                    f'padding:12px 16px;margin:8px 0;color:#e2e8f0">'
                    f'<strong>🧑 あなた:</strong> {msg["content"]}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div style="background:#14532d;border:1px solid #22c55e;border-radius:12px;'
                    f'padding:12px 16px;margin:8px 0;color:#e2e8f0">'
                    f'<strong>🤖 Gemini:</strong><br>{msg["content"]}</div>',
                    unsafe_allow_html=True,
                )

        # 入力
        g_user_input = st.chat_input("Gemini に質問...", key="gemini_input")
        g_query = g_quick_q or g_user_input

        if g_query:
            st.session_state["gemini_messages"].append({"role": "user", "content": g_query})

            try:
                from google import genai

                client = genai.Client(api_key=_gemini_key)

                # API 用メッセージ組み立て
                api_contents = []
                # 最初にシステム的な分析データを送る
                if len(st.session_state["gemini_messages"]) == 1:
                    api_contents.append({
                        "role": "user",
                        "parts": [{"text": _analysis_summary + "\n\n上記の分析データを理解した上で、以下の質問に答えてください。\n\n" + g_query}],
                    })
                else:
                    # 初回は分析データ付き、以降は会話継続
                    first_q = st.session_state["gemini_messages"][0]["content"]
                    api_contents.append({
                        "role": "user",
                        "parts": [{"text": _analysis_summary + "\n\n" + first_q}],
                    })
                    for msg in st.session_state["gemini_messages"][1:]:
                        role = "user" if msg["role"] == "user" else "model"
                        api_contents.append({
                            "role": role,
                            "parts": [{"text": msg["content"]}],
                        })

                with st.spinner("Gemini が分析中..."):
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=api_contents,
                    )
                    ai_reply = response.text

                st.session_state["gemini_messages"].append({"role": "assistant", "content": ai_reply})
                st.rerun()

            except Exception as e:
                st.error(f"Gemini エラー: {e}")
                st.session_state["gemini_messages"].pop()

        if st.session_state.get("gemini_messages"):
            if st.button("チャット履歴をクリア", key="clear_gemini"):
                st.session_state["gemini_messages"] = []
                st.rerun()
