# q1_code.py
"""Q1 深度探查：Online Retail II (UCI) —— 反常现象挖掘

在基础探查基础上，深入分析 4 类异常：
  1. Invoice 前缀（C/A 等字母前缀）的出现次数与数量特征
  2. StockCode 特殊非产品代码（POST/M/D/BANK CHARGES 等）的数量与金额占比
  3. 极端值：Quantity = 80995 / -80995、Price < 0 的完整记录
  4. 匿名 vs 实名用户：客单价、高频商品、国家分布差异
"""

import re
import numpy as np
import pandas as pd

CSV_PATH = "data/online_retail_ii.csv"
ENCODING = "ISO-8859-1"


def section(title: str) -> None:
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, encoding=ENCODING)
    # 字段名兜底（Kaggle 不同打包版本会改列名）
    if "Price" not in df.columns and "UnitPrice" in df.columns:
        df = df.rename(columns={"UnitPrice": "Price"})
    if "Customer ID" not in df.columns and "CustomerID" in df.columns:
        df = df.rename(columns={"CustomerID": "Customer ID"})
    df["line_amount"] = df["Quantity"] * df["Price"]
    return df


# ── 0. 基础探查（保留原功能） ─────────────────────────────
def basic_overview(df: pd.DataFrame) -> None:
    section("0. 基础探查")
    print(f"形状：{df.shape[0]:,} 行 × {df.shape[1]} 列")
    print(f"列名：{list(df.columns)}")

    overview = pd.DataFrame({
        "dtype":       df.dtypes.astype(str),
        "missing_pct": (df.isna().mean() * 100).round(2),
    })
    print("\n--- dtype 与缺失率 ---")
    print(overview.to_string())

    print("\n--- 数值列统计 ---")
    print(df[["Quantity", "Price"]].agg(["min", "max", "mean", "std"]).T.round(4).to_string())


# ── 1. Invoice 前缀分析 ──────────────────────────────────
def invoice_prefix_analysis(df: pd.DataFrame) -> None:
    section("1. Invoice 前缀分析（非纯数字前缀，如 C/A）")

    prefix = df["Invoice"].astype(str).str.extract(r"^([A-Za-z]+)", expand=False)
    mask = prefix.notna()
    print(f"带字母前缀的发票行数：{mask.sum():,}（占全部 {len(df):,} 行的 {mask.mean() * 100:.2f}%）")

    stats = (
        df.loc[mask]
          .assign(_prefix=prefix[mask])
          .groupby("_prefix")
          .agg(
              rows=("Invoice", "size"),
              neg_qty_ratio=("Quantity", lambda s: (s < 0).mean()),
              qty_mean=("Quantity", "mean"),
              qty_median=("Quantity", "median"),
              amount_sum=("line_amount", "sum"),
          )
          .sort_values("rows", ascending=False)
    )
    stats["neg_qty_ratio"] = (stats["neg_qty_ratio"] * 100).round(2)
    stats = stats.round(2)
    print("\n--- 各前缀统计 ---")
    print(stats.to_string())

    # TOP 3 前缀的样本
    show_cols = [c for c in ["Invoice", "StockCode", "Description", "Quantity",
                             "InvoiceDate", "Price", "Customer ID", "Country"]
                 if c in df.columns]
    for p in stats.index[:3]:
        print(f"\n--- 前缀 {p!r} 样本（前 5 行） ---")
        print(df.loc[mask & (prefix == p), show_cols].head(5).to_string(index=False))


# ── 2. StockCode 特殊代码统计 ─────────────────────────────
def stockcode_special_analysis(df: pd.DataFrame) -> None:
    section("2. StockCode 特殊非产品代码统计")

    special_codes = ["POST", "M", "D", "BANK CHARGES"]
    total_rows = len(df)
    total_abs_amount = df["line_amount"].abs().sum()

    print(f"点名特殊代码：{special_codes}\n")
    rows = []
    for code in special_codes:
        sub = df[df["StockCode"] == code]
        rows.append({
            "StockCode": code,
            "rows": len(sub),
            "row_pct(%)": round(len(sub) / total_rows * 100, 4),
            "abs_amount": round(sub["line_amount"].abs().sum(), 2),
            "amount_pct(%)": round(sub["line_amount"].abs().sum() / total_abs_amount * 100, 4),
            "qty_mean": round(sub["Quantity"].mean(), 2) if len(sub) else np.nan,
        })
    print("--- 点名代码统计（金额占比按绝对值计算，避免正负抵消） ---")
    print(pd.DataFrame(rows).to_string(index=False))

    # 补充：扫描所有"非标准"代码（不含数字，或含空格等）
    sc = df["StockCode"].astype(str).str.strip()
    non_std_mask = ~sc.str.fullmatch(r"\d+[A-Za-z]?")
    non_std = sc[non_std_mask]
    print(f"\n--- 非标准格式 StockCode：{non_std.nunique()} 个，"
          f"对应 {len(non_std):,} 行 ---")
    print("出现频次 TOP 20：")
    print(non_std.value_counts().head(20).to_string())


# ── 3. 极端值记录 ────────────────────────────────────────
def extreme_values(df: pd.DataFrame) -> None:
    section("3. 极端值记录")

    show_cols = [c for c in ["Invoice", "StockCode", "Description", "Quantity",
                             "InvoiceDate", "Price", "Customer ID", "Country"]
                 if c in df.columns]

    print("--- Quantity = 80995 或 -80995 ---")
    q = df[df["Quantity"].isin([80995, -80995])]
    print(f"共 {len(q)} 条记录")
    print(q[show_cols].to_string(index=False))

    print("\n--- Price < 0 ---")
    p = df[df["Price"] < 0]
    print(f"共 {len(p)} 条记录")
    print(p[show_cols].head(20).to_string(index=False))
    if len(p) > 20:
        print(f"... 还有 {len(p) - 20} 条，已截断")

    # 补充：负价记录的发票前缀分布，便于判断是否来自调整单
    if len(p):
        print("\n负价记录的 Invoice 前缀分布：")
        p_prefix = p["Invoice"].astype(str).str.extract(r"^([A-Za-z]+)", expand=False)
        print(p_prefix.value_counts(dropna=False).to_string())


# ── 4. 匿名 vs 实名用户对比 ───────────────────────────────
def anonymous_vs_known(df: pd.DataFrame) -> None:
    section("4. 匿名 vs 实名用户对比")

    df["is_anonymous"] = df["Customer ID"].isna()
    anon_mask = df["is_anonymous"]

    print(f"总行数：{len(df):,}")
    print(f"匿名行数：{anon_mask.sum():,}（{anon_mask.mean() * 100:.2f}%）")
    print(f"匿名发票数：{df.loc[anon_mask, 'Invoice'].nunique():,}  |  "
          f"实名发票数：{df.loc[~anon_mask, 'Invoice'].nunique():,}")

    # 客单价：按每张发票（订单）的总金额
    print("\n--- 客单价（每张 Invoice 的总金额） ---")
    order_total = df.groupby("Invoice")["line_amount"].sum()
    order_anon = df.groupby("Invoice")["is_anonymous"].first()
    for label, mask in [("匿名", order_anon), ("实名", ~order_anon)]:
        amt = order_total[mask]
        print(f"{label}：订单数 {len(amt):,}，"
              f"均值 {amt.mean():.2f}，中位数 {amt.median():.2f}，"
              f"P95 {amt.quantile(0.95):.2f}")

    # 高频商品
    print("\n--- 高频购买商品（StockCode TOP 10） ---")
    for label, mask in [("匿名", anon_mask), ("实名", ~anon_mask)]:
        top = df.loc[mask, "StockCode"].value_counts().head(10)
        print(f"\n[{label}] TOP 10 StockCode：")
        print(top.to_string())

    # 国家分布
    print("\n--- 国家分布（TOP 5，占比%） ---")
    for label, mask in [("匿名", anon_mask), ("实名", ~anon_mask)]:
        dist = (df.loc[mask, "Country"]
                .value_counts(normalize=True).head(5).mul(100).round(2))
        print(f"\n[{label}]：")
        print(dist.to_string())


def main() -> None:
    df = load_data()
    basic_overview(df)
    invoice_prefix_analysis(df)
    stockcode_special_analysis(df)
    extreme_values(df)
    anonymous_vs_known(df)


if __name__ == "__main__":
    main()