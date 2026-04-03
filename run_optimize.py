"""ローカルで重み最適化とバックテストを実行するスクリプト"""
import sys
import time

sys.path.insert(0, ".")

from modules.data import fetch_loto7_results
from modules.analysis import optimize_weights, run_backtest, FACTOR_NAMES

print("データ取得中...")
df = fetch_loto7_results()
print(f"取得完了: {len(df)} 回分\n")

# 重み最適化（30回で学習）
print("=" * 50)
print("重みの自動最適化（30回分で学習）")
print("=" * 50)
start = time.time()
weights = optimize_weights(df, test_rounds=30)
elapsed = time.time() - start

print(f"\n完了: {elapsed:.1f}秒")
print("\n最適化された重み:")
for name, w in zip(FACTOR_NAMES, weights):
    bar = "#" * int(w * 200)
    print(f"  {name:15s} {w*100:5.1f}%  {bar}")

# バックテスト（10回）
print("\n" + "=" * 50)
print("バックテスト（直近10回）")
print("=" * 50)
start = time.time()
results = run_backtest(df, last_n=10)
elapsed = time.time() - start

total_top15 = 0
total_best = 0
for r in results:
    actual = ", ".join(f"{n:02d}" for n in r["actual"])
    print(f"  第{r['round']}回: 実際[{actual}]  上位15中{r['hits_top15']}個  最高組{r['best_combo_hits']}個  全{r['all_combos_count']}組平均{r['avg_combo_hits']}個")
    total_top15 += r["hits_top15"]
    total_best += r["best_combo_hits"]

n = len(results)
print(f"\n平均: 上位15中 {total_top15/n:.1f}個的中  最高組 {total_best/n:.1f}個的中")
print(f"完了: {elapsed:.1f}秒")

print("\n結果は .optimized_weights.json と .feedback_weights.json に保存済み。")
print("git push すればクラウド版にも反映されます。")
