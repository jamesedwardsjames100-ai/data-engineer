# q1_code.py
"""Q1 基础探查：Online Retail II (UCI)

读取 data/online_retail_ii.csv，输出：
  1. 列名列表
  2. 各列 dtype 与缺失值百分比
  3. 数值列 Quantity / Price 的 min / max / mean / std
  4. 分类列 Country / StockCode 的唯一值数量与高频 TOP 10
"""

import pandas as pd

CSV_PATH = "data/online_retail_ii.csv"
ENCODING = "ISO-8859-1"   


def section(title: str) -> None:
    print(f"\n{'=' * 64}\n{title}\n{'=' * 64}")


def main() -> None:
    # ── 读入 ─────────────────────────────────────────────
    df = pd.read_csv(CSV_PATH, encoding=ENCODING)
    print(f"读取完成：{df.shape[0]:,} 行 × {df.shape[1]} 列")

    # Kaggle 各版本字段名有 Price / UnitPrice 两种命名，做一次兜底
    if "Price" not in df.columns and "UnitPrice" in df.columns:
        df = df.rename(columns={"UnitPrice": "Price"})
        print("提示：检测到 UnitPrice 列，已重命名为 Price 以便统计。")

    # ── 1. 列名 ──────────────────────────────────────────
    section("1. 列名列表")
    for i, col in enumerate(df.columns):
        print(f"  [{i:>2}] {col!r}")

    # ── 2. dtype + 缺失率 ────────────────────────────────
    section("2. 数据类型与缺失值百分比")
    overview = pd.DataFrame({
        "dtype":       df.dtypes.astype(str),
        "non_null":    df.notna().sum(),
        "missing":     df.isna().sum(),
        "missing_pct": (df.isna().mean() * 100).round(2),
    })
    print(overview.to_string())

    # ── 3. 数值列 ────────────────────────────────────────
    section("3. 数值列统计（Quantity / Price）")
    stats = (
        df[["Quantity", "Price"]]
        .agg(["min", "max", "mean", "std"])
        .T
        .round(4)
    )
    print(stats.to_string())

    # ── 4. 分类列 ────────────────────────────────────────
    section("4. 分类列唯一值数量 & 高频 TOP 10")
    for col in ["Country", "StockCode"]:
        print(f"\n--- {col} ---")
        print(f"唯一值数量：{df[col].nunique():,}")
        print("高频 TOP 10：")
        print(df[col].value_counts().head(10).to_string())


if __name__ == "__main__":
    main()