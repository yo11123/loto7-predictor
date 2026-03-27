"""ロト7の過去抽選結果を取得するモジュール"""

import requests
import pandas as pd
from bs4 import BeautifulSoup
import streamlit as st
import re
from io import StringIO
from datetime import datetime, date

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8",
}

NUMBER_MIN = 1
NUMBER_MAX = 37
MAIN_COUNT = 7
BONUS_COUNT = 2

# ロト7 第1回: 2013-04-05
FIRST_DRAW_DATE = date(2013, 4, 5)


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_loto7_results() -> pd.DataFrame | None:
    """
    ロト7の過去抽選結果を取得する（全履歴）。
    複数ソースを順に試し、最初に成功したものを返す。

    DataFrame の列:
        round (int)  : 回号
        date  (str)  : 抽選日 (YYYY-MM-DD)
        n1~n7 (int)  : 本数字 (昇順)
        b1, b2 (int) : ボーナス数字
    """
    # 1. 全履歴 CSV ソース（優先）
    for fetcher in [_fetch_from_lotolife, _fetch_from_thekyo, _fetch_from_mizuho]:
        try:
            df = fetcher()
            if df is not None and not df.empty and len(df) > 100:
                return df
        except Exception:
            continue

    # 2. フォールバック: stats247（直近100件のみ）
    try:
        df = _fetch_from_stats247()
        if df is not None and not df.empty:
            return df
    except Exception:
        pass

    return None


def _parse_japanese_csv(text: str) -> pd.DataFrame | None:
    """日本語ロト7 CSV（CP932系）の共通パーサー"""
    df = pd.read_csv(StringIO(text))

    # 列名を正規化
    rename_map = {}
    for col in df.columns:
        c = str(col).strip()
        if re.search(r"開催回|回号|回数", c):
            rename_map[col] = "round"
        elif re.search(r"開催日|抽選日|日付", c):
            rename_map[col] = "date"
        elif re.search(r"ボーナス.*?1|BONUS.*?1", c, re.I):
            rename_map[col] = "b1"
        elif re.search(r"ボーナス.*?2|BONUS.*?2", c, re.I):
            rename_map[col] = "b2"
        else:
            m = re.search(r"第(\d)数字|本数字(\d)|NUM(\d)", c, re.I)
            if m:
                idx = next(g for g in m.groups() if g)
                rename_map[col] = f"n{int(idx)}"

    df = df.rename(columns=rename_map)

    required = [f"n{i}" for i in range(1, 8)]
    if not all(c in df.columns for c in required):
        return None

    if "round" not in df.columns:
        df["round"] = range(1, len(df) + 1)

    for col in required:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["round"] = pd.to_numeric(df["round"], errors="coerce")
    df = df.dropna(subset=required + ["round"])
    for col in required:
        df[col] = df[col].astype(int)
    df["round"] = df["round"].astype(int)

    for col in ["b1", "b2"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")

    cols = ["round", "date"] + required + ["b1", "b2"]
    cols = [c for c in cols if c in df.columns]
    df = df[cols].drop_duplicates("round").sort_values("round").reset_index(drop=True)
    return df


def _fetch_from_lotolife() -> pd.DataFrame | None:
    """loto-life.net から全履歴 CSV を取得"""
    url = "https://loto-life.net/csv/loto7"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    text = resp.content.decode("cp932", errors="replace")
    return _parse_japanese_csv(text)


def _fetch_from_thekyo() -> pd.DataFrame | None:
    """loto7.thekyo.jp から全履歴 CSV を取得"""
    url = "https://loto7.thekyo.jp/data/loto7.csv"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    text = resp.content.decode("cp932", errors="replace")
    return _parse_japanese_csv(text)


def _fetch_from_mizuho() -> pd.DataFrame | None:
    """みずほ銀行公式から全履歴 CSV を取得"""
    url = "https://www.mizuhobank.co.jp/retail/takarakuji/loto/loto7/csv/loto7.csv"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    text = resp.content.decode("cp932", errors="replace")
    return _parse_japanese_csv(text)


def _fetch_from_stats247() -> pd.DataFrame | None:
    """
    stats247.com からロト7の直近100件の結果を取得する。
    <li class="lg-number"> が本数字、
    <li class="lg-number lg-reversed"> がボーナス数字。
    """
    url = "https://stats247.com/lotto/japan-takarakuji-7"
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # 2列目の table (Date | Draw Results)
    tables = soup.find_all("table")
    target_table = None
    for tbl in tables:
        headers_row = tbl.find("tr")
        if headers_row:
            ths = [th.get_text(strip=True) for th in headers_row.find_all(["th", "td"])]
            if "Date" in ths and "Draw Results" in ths:
                target_table = tbl
                break

    if target_table is None:
        raise ValueError("結果テーブルが見つかりません")

    rows = []
    for tr in target_table.find_all("tr")[1:]:  # ヘッダーをスキップ
        tds = tr.find_all("td")
        if len(tds) < 2:
            continue

        # 日付 (dd-mm-yyyy)
        date_text = tds[0].get_text(strip=True)
        m = re.match(r"(\d{2})-(\d{2})-(\d{4})", date_text)
        if not m:
            continue
        d, mo, y = m.groups()
        date_str = f"{y}-{mo}-{d}"

        # 本数字とボーナス数字を li タグから抽出
        ul = tds[1].find("ul")
        if not ul:
            continue
        main_nums = []
        bonus_nums = []
        for li in ul.find_all("li"):
            classes = li.get("class", [])
            num_text = li.get_text(strip=True)
            if not num_text.isdigit():
                continue
            n = int(num_text)
            if not (NUMBER_MIN <= n <= NUMBER_MAX):
                continue
            if "lg-reversed" in classes:
                bonus_nums.append(n)
            else:
                main_nums.append(n)

        if len(main_nums) != MAIN_COUNT:
            continue

        row = {"date": date_str}
        for i, n in enumerate(sorted(main_nums), 1):
            row[f"n{i}"] = n
        for i, n in enumerate(bonus_nums[:BONUS_COUNT], 1):
            row[f"b{i}"] = n

        rows.append(row)

    if not rows:
        return None

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # 日付から回号を推定 (第1回: 2013-04-05, 以降週1回)
    df["round"] = df["date"].apply(_estimate_round)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    # 列順を整える
    cols = ["round", "date"] + [f"n{i}" for i in range(1, 8)] + ["b1", "b2"]
    cols = [c for c in cols if c in df.columns]
    return df[cols]


def _estimate_round(draw_date) -> int:
    """
    抽選日から回号を推定する。
    第1回: 2013-04-05。以降ほぼ毎週金曜日。
    週数で割り算して近似値を返す。
    """
    if hasattr(draw_date, "date"):
        d = draw_date.date()
    elif isinstance(draw_date, str):
        d = datetime.strptime(draw_date, "%Y-%m-%d").date()
    else:
        d = draw_date
    delta = (d - FIRST_DRAW_DATE).days
    return max(1, round(delta / 7) + 1)


def parse_uploaded_csv(uploaded_file) -> pd.DataFrame | None:
    """
    ユーザーがアップロードした CSV をパースする。

    対応フォーマット例:
        回号,抽選日,第1数字,第2数字,...,第7数字,ボーナス1,ボーナス2
    """
    try:
        content = uploaded_file.read().decode("utf-8-sig")
        df = pd.read_csv(StringIO(content))

        rename_map = {}
        for col in df.columns:
            col_clean = str(col).strip()
            if re.search(r"回[号数]?|round", col_clean, re.I):
                rename_map[col] = "round"
            elif re.search(r"日|date", col_clean, re.I):
                rename_map[col] = "date"
            else:
                # 本数字列: 第1数字, n1, 数字1 など
                m = re.search(r"第?(\d).*?数字|^n(\d)$|数字(\d)", col_clean, re.I)
                if m:
                    idx = next(g for g in m.groups() if g)
                    rename_map[col] = f"n{idx}"
                    continue
                # ボーナス列
                mb = re.search(r"ボーナス.*?(\d)|bonus.*?(\d)|^b(\d)$", col_clean, re.I)
                if mb:
                    idx = next(g for g in mb.groups() if g)
                    rename_map[col] = f"b{idx}"

        df = df.rename(columns=rename_map)

        # 必須列チェック
        required = [f"n{i}" for i in range(1, 8)]
        for col in required:
            if col not in df.columns:
                st.error(f"列 '{col}' が見つかりません。CSVのフォーマットを確認してください。")
                return None

        # round 列がなければ行番号で付与
        if "round" not in df.columns:
            df["round"] = range(1, len(df) + 1)

        for col in required:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype(int)
        df["round"] = pd.to_numeric(df["round"], errors="coerce").astype(int)

        for col in ["b1", "b2"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

        df = df.drop_duplicates("round").sort_values("round").reset_index(drop=True)
        return df

    except Exception as e:
        st.error(f"CSV パースエラー: {e}")
        return None


def refresh_results() -> pd.DataFrame | None:
    """キャッシュをクリアして最新データを再取得する"""
    fetch_loto7_results.clear()
    return fetch_loto7_results()


def get_main_numbers(df: pd.DataFrame) -> list[list[int]]:
    """各行の本数字7個をリストのリストで返す"""
    cols = [f"n{i}" for i in range(1, 8)]
    return df[cols].values.tolist()
