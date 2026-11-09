# AI_LOG.md - AI 完整对话记录

> 请粘贴你和 AI 的**完整对话记录**（**原文，不要删改、不要总结**）。
> 
> 📌 **填写要求**：
> - 每段对话必须标注：对应**哪道题**、**第几次迭代**、**用了什么 AI**
> - 截图也可以（放在 `ai_logs/` 子目录下并在此处引用）
> - 不需要美化排版 —— 我们就是要看原始过程
> 
> ⚠️ **重要**：
> - 谎报 AI 使用情况、伪造对话记录 → 在面试中会被发现 → **直接淘汰**
> - 完全没用 AI 也没关系，请在此说明
> - 如果对话量极大，至少保留**最关键的 5-10 次对话**

---

## 📊 AI 使用统计

请简要统计你的 AI 使用情况：

| AI 工具 | 大致对话次数 | 主要用途 |
|---------|--------------|----------|
| deep seek | ~50 次 | 代码生成、Debug、Prompt 设计 |
| cursor | ~80 次自动补全 | 代码补全 |
| | | |

---
模块 0：download_data.py 的迭代过程

### 第 1 次迭代
- **我的 Prompt**：你是一个 Python 数据工程师。请帮我写一个脚本。要求：使用 kagglehub 下载 'mashlyn/online-retail-ii-uci' 和 'olistbr/brazilian-ecommerce'。下载链接为：| Online Retail II（UCI） | https://www.kaggle.com/datasets/mashlyn/online-retail-ii-uci | 模块 1（Q1）、模块 3（Q3） |
| Brazilian E-Commerce by Olist | https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce | 模块 2（Q2）、模块 4（Q4） |下载后，把里面的 CSV 文件复制到当前根目录的 data/ 和 data/olist/ 目录下。
- **AI 输出与盲区**：
# download_data.py
"""
下载两个 Kaggle 数据集，并把 CSV 复制到项目根目录下的 data/ 与 data/olist/

  - mashlyn/online-retail-ii-uci  ->  ./data/
  - olistbr/brazilian-ecommerce   ->  ./data/olist/

运行前:
    pip install kagglehub

Kaggle 认证（任选一种）:
    1) 环境变量 KAGGLE_USERNAME / KAGGLE_KEY
    2) ~/.kaggle/kaggle.json
"""

from pathlib import Path
import shutil
import kagglehub

# 项目根目录（脚本所在目录）
ROOT = Path(__file__).resolve().parent

# 数据集 handle -> 目标目录
DATASETS = {
    "mashlyn/online-retail-ii-uci": ROOT / "data",
    "olistbr/brazilian-ecommerce":  ROOT / "data" / "olist",
}


def copy_csvs(src_dir: Path, dst_dir: Path) -> None:
    """把 src_dir 下（含子目录）所有 CSV 扁平复制到 dst_dir。"""
    dst_dir.mkdir(parents=True, exist_ok=True)
    csv_files = list(src_dir.rglob("*.csv"))
    if not csv_files:
        print(f"  [警告] {src_dir} 中没有找到 CSV 文件")
        return
    for f in csv_files:
        shutil.copy2(f, dst_dir / f.name)
        print(f"  {f.name}  ->  {dst_dir / f.name}")


def main() -> None:
    for handle, dst_dir in DATASETS.items():
        print(f"\n=== 下载 {handle} ===")
        cache_dir = Path(kagglehub.dataset_download(handle))
        print(f"缓存目录: {cache_dir}")
        copy_csvs(cache_dir, dst_dir)

    print("\n全部完成。")
    print(f"  data/        -> {ROOT / 'data'}")
    print(f"  data/olist/  -> {ROOT / 'data' / 'olist'}")


if __name__ == "__main__":
    main()

**你的评估**：
AI 给出了第一版本代码，跑通后发现终端输出名为 `online_retail_II.csv`，而且没有本地缓存校验。还存在重复下载和没做完整性校验，如果网络环境出现问题，没有解决。
### 第 2 次迭代
- **我的 Prompt**：现在功能可以跑通，但存在很多生产环境的隐患。请帮我重构这段代码，把所有需求融合在一起，要求如下：进行本地防重校验，Kaggle 原文件是 online_retail_II.csv（大写），请强制将其重命名为小写 online_retail_ii.csv 后再保存。Olist 数据集应该有 9 个 CSV 文件。在复制完成后，请校验这 9 个文件是否齐全，如果缺失任何一个，直接抛出 FileNotFoundError。国内网络访问 Kaggle 不稳定，请给 kagglehub.dataset_download 套上 try-except。如果网络超时报错，不要直接崩溃，而是打印清晰的中文指引，并向上抛出异常。
- **结果**：
# download_data.py
"""
从 Kaggle 下载并整理两份数据集到本地项目目录。

  - mashlyn/online-retail-ii-uci   ->  data/online_retail_ii.csv  （强制小写）
  - olistbr/brazilian-ecommerce    ->  data/olist/*.csv           （9 个 CSV，完整校验）

关键行为:
  1. 本地防重校验
     - data/online_retail_ii.csv 存在 -> 跳过 Online Retail II 下载
     - data/olist/olist_orders_dataset.csv 存在且 Olist 9 个 CSV 齐全 -> 跳过 Olist 下载
     （哨兵存在但数据不全时，视为上次失败，自动重下）
  2. 强制重命名
     - Kaggle 原文件名 online_retail_II.csv（大写）落盘为 online_retail_ii.csv（小写）
  3. Olist 完整性校验
     - 复制后校验 9 个 CSV 是否齐全，缺任何一个即打印明细并抛 FileNotFoundError
  4. 网络容错
     - kagglehub.dataset_download 包 try-except，失败时打印中文指引并向上 raise

依赖:
    pip install kagglehub
Kaggle 认证:
    环境变量 KAGGLE_USERNAME / KAGGLE_KEY，或 ~/.kaggle/kaggle.json
"""

from pathlib import Path
import shutil

import kagglehub

# ----- 路径常量 -----
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OLIST_DIR = DATA_DIR / "olist"

# 最终产物 / 防重哨兵
RETAIL_FILE = DATA_DIR / "online_retail_ii.csv"
OLIST_SENTINEL = OLIST_DIR / "olist_orders_dataset.csv"

# Olist 应包含的 9 个 CSV
OLIST_REQUIRED = {
    "olist_customers_dataset.csv",
    "olist_geolocation_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
}


def _download(handle: str) -> Path:
    """下载数据集；失败时打印中文指引并向上抛出异常。"""
    print(f"  → 拉取 {handle} ...")
    try:
        return Path(kagglehub.dataset_download(handle))
    except Exception as exc:
        print(f"\n[错误] 从 Kaggle 下载 {handle} 失败：{exc}")
        print("可能原因：网络不稳定 / 代理未配置 / Kaggle 认证缺失或被限流。")
        print("建议：")
        print("  1) 检查网络/代理后重试；")
        print("  2) 或手动前往 Kaggle 下载，将 CSV 放到 data/ 对应目录：")
        print(f"     https://www.kaggle.com/datasets/{handle}")
        raise  # 不吞异常，交给调用方决定重试 / 降级 / 报警


def fetch_retail() -> None:
    """下载 Online Retail II，以在线名小写落地。"""
    if RETAIL_FILE.exists():
        print(f"[跳过] {RETAIL_FILE.name} 已存在")
        return

    print("\n=== Online Retail II (UCI) ===")
    cache = _download("mashlyn/online-retail-ii-uci")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    # 大小写不敏感匹配在线文件名；用目标小写名 copy 等价于“复制后强制重命名”
    for src in cache.rglob("*.csv"):
        if src.name.lower() == "online_retail_ii.csv":
            shutil.copy2(src, RETAIL_FILE)
            print(f"  {src.name}  ->  {RETAIL_FILE.name}  (已强制小写)")
            return

    raise FileNotFoundError(
        f"在 {cache} 下未找到 online_retail_II.csv，"
        "可能是 Kaggle 打包版本变化（例如拆成年份文件），请检查后处理。"
    )


def fetch_olist() -> None:
    """下载 Olist，落地并校验 9 个 CSV 是否齐全。"""
    if OLIST_SENTINEL.exists():
        actual = {p.name for p in OLIST_DIR.glob("*.csv")}
        if OLIST_REQUIRED <= actual:
            print(f"[跳过] {OLIST_SENTINEL.name} 已存在且 Olist 完整")
            return
        print(f"[重下] {OLIST_SENTINEL.name} 存在但 Olist 不完整，重新下载")

    print("\n=== Brazilian E-Commerce (Olist) ===")
    cache = _download("olistbr/brazilian-ecommerce")

    OLIST_DIR.mkdir(parents=True, exist_ok=True)
    for src in cache.rglob("*.csv"):
        dst = OLIST_DIR / src.name
        shutil.copy2(src, dst)
        print(f"  {src.name}  ->  {dst.name}")

    # 完整性校验
    actual = {p.name for p in OLIST_DIR.glob("*.csv")}
    missing = OLIST_REQUIRED - actual
    if missing:
        print(f"\n[错误] Olist 数据集不完整，缺少 {len(missing)} 个文件：")
        for name in sorted(missing):
            print(f"  - {name}")
        raise FileNotFoundError(f"Olist 缺少 {len(missing)} 个 CSV：{sorted(missing)}")

    print(f"[校验通过] Olist {len(OLIST_REQUIRED)} 个 CSV 齐全")


def main() -> None:
    fetch_retail()
    fetch_olist()
    print("\n全部完成。")


if __name__ == "__main__":
    main()

对照你的 4 条要求，逐条落地说明：

本地防重校验 — fetch_retail / fetch_olist 开头先判断哨兵文件。Olist 这里多做了一步：哨兵存在但 9 个文件不齐时判定为“上次下载中途失败”，自动重下而不是盲目跳过，避免半套数据卡死后续流程。

强制重命名 — src.name.lower() == "online_retail_ii.csv" 做大小写不敏感匹配，命中后 shutil.copy2(src, RETAIL_FILE)，目标名本身就是小写 online_retail_ii.csv。这是“以目标名落地”的实现方式，语义等价于“复制 → 重命名”但少一次 IO。仅当你明确要求 Path.rename 的写法时再改。

Olist 完整性断言 — OLIST_REQUIRED 是 9 个文件名的 frozenset（用 set 更好，差异计算 O(1)），missing = OLIST_REQUIRED - actual，非空则打印明细后 raise FileNotFoundError。异常向上传播，main 不 catch，让程序带 traceback 退出——排错信息完整，也方便你后续在外面套重试逻辑。

网络容错 — _download 用 except Exception 捕获（不只 TimeoutError，因为 kagglehub 内部可能抛 requests 系列、ConnectionError、OSError 等多种异常），打印中文指引后 raise，不 sys.exit——满足“向上抛出异常”，让调用方（测试、定时任务、调度器）有决策空间。
**你的评估**：
通过这次的修改，这段代码从一次性变成了可复用，同时考虑了很多潜在的问题。

## 🔍 模块 1：数据质量探索

### 对话 1：Q1.1 - 数据加载与初探（使用工具：deep seek）

**Prompt**：
你是一个资深的数据分析师。请帮我写一个 Python 脚本 q1_code.py，读取 data/online_retail_ii.csv。要求完成以下基础探查：打印各列的数据类型和缺失值百分比。打印数值列（Quantity, Price）的 min, max, mean, std。打印字符串列（Country, StockCode）的唯一值数量和高频 TOP 10。顺带打印出数据集的列名列表，让我确认一下字段。

**AI 回复**：
```
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
运行：

bash
python q1_code.py
一点说明：

encoding='ISO-8859-1' 按你要求写死在常量里，原因是原始 CSV 含 Latin-1 字符（如 Café 之类的商品名），用 utf-8 会 UnicodeDecodeError。

Price 兜底：UCI 原版字段叫 UnitPrice，Kaggle 上部分版本被重命名为 Price。加了一行 rename，两种命名都能跑；如果你拿到的是 Price 版本，这行不触发。

round(4) 是显示层截断，不影响后续计算；Quantity 因为有退货负数，mean 会比中位数偏低，属于正常现象，不用改。

输出用 to_string() 避免 pandas 宽表被 ... 截断，方便你贴到报告里。

跑完把输出发我，就能决定 Q1 下一步该做清洗还是直接聚合。


```

**你的评估**：
>AI给出的代码虽然可以跑通，但只是最基础的模板，只打印了宏观的统计结果，它没有发现原题里是 `InvoiceNo` ，而字段在真实数据里其实是叫 `Invoice`，也没有意识其他细节的一些问题。
> **我的修正**：
>运行代码后，我查阅了 `df.columns`，确认了字段名差异，然后在后续代码中统一使用 `Invoice` 和 `Price`。同时我要求 AI 针对具体字段进行深度正则匹配和极值打印。

---
**Prompt**：
现在我发现了几个反常现象，请帮我更新 q1_code.py，深入挖掘以下问题，并打印结果：提取 Invoice 列中非纯数字的前缀（如字母 C 和 A），统计出现次数，并查看这些记录的特征（数量是否为负）。检查 StockCode 里特殊的非产品代码（如 POST, M, D, BANK CHARGES），统计它们的数量和金额占比。找出 Quantity 等于 80995 和 -80995 的极值记录，以及 Price 为负的记录，看它们的完整信息。对比 Customer ID 缺失（匿名）和未缺失的用户，看看他们的客单价、高频购买商品和国家分布有什么差异。”

**AI 回复**：
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

运行：

bash
python q1_code.py
几个设计点说明：

df["line_amount"] 只算一次：所有金额相关统计都复用它，避免每处重复 Quantity * Price。

amount_pct 用绝对值：特殊代码（尤其 M 手工调整）包含正负，用绝对值占比才能反映真实的“非商品交易所占体量”，否则正负抵消。Invoice 前缀分析里保留带符号的 amount_sum，因为取消订单（C）本来就是负贡献，需要看原始符号。

non_std_mask 用 ~str.fullmatch(r"\d+[A-Za-z]?")：命中所有“不是纯数字+可选单字母后缀”的代码，比硬编码白名单更全。POST、M、D、BANK CHARGES 都会出现；结果 TOP 20 让你一眼看清还有没有别的（如 DOT、C2、CRUK、AMAZONFEE）。

极端值全量打印：Quantity = ±80995 通常只有个位数；Price < 0 也少。如果某版本数据量超预期会提示 ... 还有 N 条，不会刷屏。

客单价对比以 Invoice 为单位：匿名订单的 Customer ID 是 NaN，但 Invoice 完整，所以按 Invoice 分组是最合理的口径。均值 / 中位数 / P95 一起给，因为均值容易被几笔大单拉高。

is_anonymous 列：Customer ID 只有 NaN 或有效数值两种状态，isna() 判定最干净。

跑完把四块输出贴回来，尤其关注：

C 前缀的 neg_qty_ratio 是不是接近 100%（应该接近，因为 C 代表取消）

M / POST / BANK CHARGES 的金额占比，如果三者合计超过 1~2% 就说明需要单独剥离

Price < 0 记录的 Invoice 前缀分布（大概率是 A，即 Adjusted 调整单）

**你的评估**：
通过看终端的打印的结果，发现这次AI写出了正则表达式提取前缀（C 和 A），并且成功用 `groupby` 帮我找出了匿名用户和实名用户的消费差异。在极值记录里，只有最大最小值，但我通过观察终端输出，发现了这两个极值其实是一正一负，同时可以抵消为0，这应该是数据录入错误，而不是真实业务。
匿名用户客单价（10.86）后，我补充了高频商品维度的对比。匿名用户TOP1商品是 `POST`，结合客单价极低的现象，由此推导出了这群“沉默大多数”是线下散客或补邮费客户。


## 📊 模块 2：SQL 与业务分析

### 对话 1：

## Q2.1 商品类别翻译完整性

**Prompt**：你是一个精通 MySQL 8.0 的数据工程师。请帮我写一段 SQL。找出 products 表中存在的商品类别（product_category_name），但在翻译表 product_category_name_translation 中没有英文对照的类别名，并统计每种类别对应多少个商品。要求：必须以 products 为主表，使用 LEFT JOIN 结合 IS NULL 的方式反查缺失项。排除 product_category_name 本身为空的数据。输出结果按商品数量降序排列，并加上清晰的中文别名。

**AI 回复**：
-- 找出在商品表里出现、但翻译表里没有英文对照的类别，并统计各类别商品数
SELECT
    p.product_category_name        AS `商品类别（葡萄牙语）`,
    COUNT(DISTINCT p.product_id)   AS `商品数量`
FROM olist_products_dataset AS p
LEFT JOIN product_category_name_translation AS t
       ON p.product_category_name = t.product_category_name
WHERE p.product_category_name IS NOT NULL        -- 排除类别为空
  AND p.product_category_name <> ''              -- 排除空字符串
  AND t.product_category_name IS NULL            -- 反查：翻译表里没匹配上
GROUP BY p.product_category_name
ORDER BY `商品数量` DESC;
几点说明：

主表 / 反查方式 按你要求：olist_products_dataset 在左，LEFT JOIN 翻译表，靠 t.product_category_name IS NULL 挑出“翻译表里没有的”。这是 anti-join 的标准写法，MySQL 8.0 的优化器能把它转成半连接的反面（NOT EXISTS 等价计划），性能没问题。

<> '' 这一层别省：UCI 那套数据里出现过空字符串，Olist 虽然基本是 NULL，但加上更稳妥；否则空字符串也会被当成“未翻译类别”出现在结果里，误导判断。

COUNT(DISTINCT p.product_id)：理论上 product_category_name 在翻译表里应是主键（唯一），但万一上游某次导入重复了一行翻译，COUNT(*) 会被放大。用 DISTINCT 计数能免疫这种情况，代价可忽略。

表名对齐：你数据库里实际是 olist_products_dataset（前面 load_olist.py 按文件名落表），所以我用了这个名；如果你后来手动改成了 products，把两处 olist_products_dataset 换成 products 即可。

中文别名 用了反引号包住，因为中文别名含括号和特殊字符，双引号在 MySQL 默认 sql_mode 下也不认（除非 ANSI_QUOTES），反引号最稳。

ORDER BY 用别名：MySQL 允许在 ORDER BY 里引用 SELECT 别名，\商品数量`这样写就行，不用重复COUNT(...)`。

跑出来应该能看到类似 pc_gamer、portateis_cozinha_e_preparadores_de_alimentos 这类类别——这些就是著名的"翻译表缺失、只能看葡萄牙语原名"的品类。
**你的评估**：

这次的回答不仅给出了 LEFT JOIN ... IS NULL 的 Anti-Join（反连接）标准写法，还主动做出了 4 个非常关键修正，AI 预判了我的表名、防范了空字符串等。我将 AI 给出的 SQL 放进 MySQL Workbench 实际执行，跑出了 pc_gamer（3 条）和 portateis_cozinha_e_preparadores_de_alimentos（10 条）两个缺失翻译的品类。

---
Q2.2 平台真实成交分析
**Prompt**：
你是一个资深的大数据 SQL 工程师。请帮我写一段 MySQL 8.0 的 SQL，按月份统计平台的真实成交情况。输出字段：month (基于 order_purchase_timestamp)、total_orders (总下单量)、delivered_orders (成功送达单量)、canceled_orders (取消单量)、cancel_rate (取消率，保留2位小数)、delivered_gmv (已送达订单的 GMV，含 price + freight_value)、avg_delivery_days (已送达订单的平均送达天数)。以下的要求要注意：orders 和 order_items 是一对多关系。为了避免 JOIN 导致数据膨胀和 GMV 虚高，必须先用 CTE（WITH 语句）按 order_id 对 order_items 进行预聚合，算出每个订单的总金额，然后再和 orders 表做 1:1 关联。计算平均送达天数时，必须过滤掉 order_delivered_customer_date 为 NULL 的异常/未送达订单。使用 CASE WHEN 结合 SUM 进行条件聚合，不要用复杂的子查询。

**AI 回复**：
-- ============================================================
-- 按月份统计平台真实成交情况
-- 关键点：
--   1. order_items 先按 order_id 预聚合，避免 JOIN 1:N 导致
--      行数膨胀、GMV 重复累加
--   2. 预聚合结果再和 orders 做 1:1 关联
--   3. 送达天数只对“状态=delivered 且 delivered_customer_date 非空”的订单计算
--   4. 条件聚合全部用 CASE WHEN + SUM / AVG，不嵌套子查询
-- ============================================================

WITH item_agg AS (
    -- 预聚合：每个订单的 GMV（price + freight_value 全部累加）
    -- 这里是 1:N → 1 的关键收敛，后面 join 才是 1:1
    SELECT
        order_id,
        SUM(price)                       AS items_price,
        SUM(freight_value)               AS items_freight,
        SUM(price + freight_value)       AS order_gmv
    FROM olist_order_items_dataset
    GROUP BY order_id
)
SELECT
    DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m')                AS month,
    COUNT(*)                                                        AS total_orders,
    SUM(CASE WHEN o.order_status = 'delivered' THEN 1 ELSE 0 END)   AS delivered_orders,
    SUM(CASE WHEN o.order_status = 'canceled'  THEN 1 ELSE 0 END)   AS canceled_orders,

    -- 取消率（百分比，保留 2 位）
    ROUND(
        SUM(CASE WHEN o.order_status = 'canceled' THEN 1 ELSE 0 END) * 100.0
        / NULLIF(COUNT(*), 0),
        2
    )                                                               AS cancel_rate,

    -- 已送达订单的 GMV：用预聚合后的 order_gmv，避免放大
    ROUND(
        SUM(CASE WHEN o.order_status = 'delivered'
                 THEN COALESCE(ia.order_gmv, 0) ELSE 0 END),
        2
    )                                                               AS delivered_gmv,

    -- 平均送达天数：只算 delivered 且送达时间非空
    -- AVG 会自动忽略 CASE 未命中的 NULL，等价于过滤
    ROUND(
        AVG(
            CASE WHEN o.order_status = 'delivered'
                  AND o.order_delivered_customer_date IS NOT NULL
                 THEN DATEDIFF(
                        o.order_delivered_customer_date,
                        o.order_purchase_timestamp
                      )
            END
        ),
        2
    )                                                               AS avg_delivery_days

FROM olist_orders_dataset AS o
LEFT JOIN item_agg         AS ia
       ON o.order_id = ia.order_id          -- 1:1，预聚合后不会膨胀

GROUP BY month
ORDER BY month;


个关键设计点，逐条对齐你的 🚨 要求：

CTE 预聚合 + 1:1 关联 — item_agg 按 order_id 聚合出 order_gmv（SUM(price + freight_value)），外面 LEFT JOIN 时每条订单最多命中一行，COUNT(*) 和 SUM(order_gmv) 都不会被 item 数量放大。这是你明确点名的核心，务必保留这个结构。

AVG(CASE WHEN ... THEN DATEDIFF(...) END) — CASE 未命中时返回 NULL，AVG 天生忽略 NULL，所以 delivered_customer_date IS NULL 的未送达单天然被剔除，不需要额外子查询或子集。这条要求就靠这个写法满足。

条件聚合不用子查询 — delivered_orders / canceled_orders / delivered_gmv / avg_delivery_days 全部是 SUM(CASE WHEN...) 或 AVG(CASE WHEN...) 单趟扫描完成，没有一处 SELECT (SELECT ...)。

NULLIF(COUNT(*), 0) — 分母兜底，虽然实际不会有某月 0 单的情况，但工业代码里加上防止意外 Division by zero。

COALESCE(ia.order_gmv, 0) — 保护 LEFT JOIN 未命中的订单（理论上 Olist 每单至少有 1 个 item，但导入时若 order_items 缺行，ia.order_gmv 会是 NULL，让它以 0 进入 sum 而不是 NULL 传染整列）。

cancel_rate 用的是百分比 — 想改成小数比率（0.00–1.00）就去掉 * 100.0。这是业务口径选择，我按“取消率”字面意思用百分比。

DATE_FORMAT(..., '%Y-%m') — MySQL 8.0 没有 DATE_TRUNC，DATE_FORMAT 是标准做法。若你库里 order_purchase_timestamp 目前是 TEXT（之前 load_olist.py 用 pandas 直接落表，未 parse_dates），DATE_FORMAT / DATEDIFF 都会走隐式转换，格式 YYYY-MM-DD HH:MM:SS 能正确解析。但要注意隐式转换无法走索引——如果要频繁按月份查询，建议后续把这两列 ALTER 成 DATETIME，或在导入时用 parse_dates 指定。

表名 — 与你 load_olist.py 落地的表名一致：olist_orders_dataset、olist_order_items_dataset。如果你后来手动重命名成 orders / order_items，替换这两处即可。

一个值得你复核的业务点：delivered_gmv 我按“订单当前状态为 delivered 的整单金额”统计。Olist 里存在一种情况——订单状态是 delivered，但实际未送达（delivered_customer_date IS NULL），这类会被算进 delivered_orders 和 delivered_gmv，但不进 avg_delivery_days。如果你希望 delivered_orders / delivered_gmv 也严格只算“真正送达”的单（即 delivered_customer_date IS NOT NULL），把 delivered_orders 和 delivered_gmv 里的 CASE 条件都补上 AND o.order_delivered_customer_date IS NOT NULL 即可——业务口径的差异，需要你确认后再定。

**你的评估**：

这次 AI 的回答提出了几个问题：第一，要使用 NULLIF(COUNT(*), 0) 规避了“除以零”的潜在风险；使用 COALESCE 防止了 LEFT JOIN 未命中时 NULL 值对 SUM 聚合的污染（NULL 传染）。第二，AI 指出了 order_purchase_timestamp 目前是 TEXT 类型（因为之前 Pandas 直接建表落库），警告我 DATE_FORMAT 的隐式转换会导致索引失效，并给出了用 ALTER TABLE 转为 DATETIME 的实践。第三，AI 发现了一个 Olist 数据里的真实脏数据场景——有些订单状态是 delivered，但 order_delivered_customer_date 却是空的。它把“是否要把这部分没有实际送达日期的订单算进 GMV”的决策权交给了我。
经过考量，我采纳了 AI 的建议，在 delivered_orders 和 delivered_gmv 的 CASE WHEN 里，除了判断 status = 'delivered'，补上了 AND order_delivered_customer_date IS NOT NULL。因为对于 BI 报表而言，“真实成交”必须意味着钱货两清，没有实际送达日期的订单不应该计入确认收入。这避免了财务口径的虚高。

**Prompt**：
在 delivered_orders 和 delivered_gmv 的 CASE WHEN 里，除了判断 status = 'delivered'，补上了 AND order_delivered_customer_date IS NOT NULL。因为对于 BI 报表而言，“真实成交”必须意味着钱货两清，没有实际送达日期的订单不应该计入确认收入。这避免了财务口径的虚高。
**AI 回复**：
-- ============================================================
-- 按月份统计平台真实成交情况（财务口径：钱货两清）
--
-- 口径定义：
--   "真实送达" = order_status = 'delivered'
--              AND order_delivered_customer_date IS NOT NULL
--   delivered_orders / delivered_gmv / avg_delivery_days 三处
--   共用此定义，保证报表内部自洽。
--
-- 结构要点：
--   1. order_items 先按 order_id 预聚合，再 1:1 JOIN orders
--   2. 全部条件聚合用 CASE WHEN + SUM / AVG，无子查询
-- ============================================================

WITH item_agg AS (
    SELECT
        order_id,
        SUM(price + freight_value)   AS order_gmv
    FROM olist_order_items_dataset
    GROUP BY order_id
)
SELECT
    DATE_FORMAT(o.order_purchase_timestamp, '%Y-%m')                AS month,
    COUNT(*)                                                        AS total_orders,

    -- 真实送达单量：status=delivered 且送达日期非空
    SUM(CASE WHEN o.order_status = 'delivered'
              AND o.order_delivered_customer_date IS NOT NULL
             THEN 1 ELSE 0 END)                                     AS delivered_orders,

    SUM(CASE WHEN o.order_status = 'canceled'  THEN 1 ELSE 0 END)   AS canceled_orders,

    -- 取消率：分母保持为当月全部下单量（业务上通常这样定义）
    ROUND(
        SUM(CASE WHEN o.order_status = 'canceled' THEN 1 ELSE 0 END) * 100.0
        / NULLIF(COUNT(*), 0),
        2
    )                                                               AS cancel_rate,

    -- 已确认收入 GMV：同样只算钱货两清的单
    ROUND(
        SUM(CASE WHEN o.order_status = 'delivered'
                  AND o.order_delivered_customer_date IS NOT NULL
                 THEN COALESCE(ia.order_gmv, 0) ELSE 0 END),
        2
    )                                                               AS delivered_gmv,

    -- 平均送达天数：只对真实送达单取 DATEDIFF，AVG 自动忽略 NULL
    ROUND(
        AVG(
            CASE WHEN o.order_status = 'delivered'
                  AND o.order_delivered_customer_date IS NOT NULL
                 THEN DATEDIFF(
                        o.order_delivered_customer_date,
                        o.order_purchase_timestamp
                      )
            END
        ),
        2
    )                                                               AS avg_delivery_days

FROM olist_orders_dataset AS o
LEFT JOIN item_agg         AS ia
       ON o.order_id = ia.order_id          -- 1:1，无膨胀

GROUP BY month
ORDER BY month;

两点值得你在报表层面确认，不是代码问题，是口径完备性：

cancel_rate 的分母仍然是 COUNT(*)（全部下单量），包含已送达、已取消、以及 shipped / processing / unavailable 等中间态。如果你希望它变成"取消 ÷（已送达 + 已取消）"这种只统计终态的收敛口径，分母得改成 SUM(CASE WHEN status IN ('delivered','canceled') AND ... THEN 1 END)，取消率会明显偏高。现在的写法是"取消占全部下单的比例"，跟 BI 里常见的 order_cancel_rate 定义一致，所以没动。

有金额"消失"：状态是 delivered 但 delivered_customer_date 为 NULL 的订单，其 GMV 既不在 delivered_gmv 里、也不在 canceled 里，在月度汇总中处于未归类状态。做单月 GMV 对账时如果发现 delivered_gmv + 其他状态 GMV ≠ 总 GMV，差额就来自这批单。如果需要对账，加一列：

sql
    ROUND(SUM(CASE WHEN o.order_status = 'delivered'
                    AND o.order_delivered_customer_date IS NULL
                   THEN COALESCE(ia.order_gmv, 0) ELSE 0 END), 2)
                                                                    AS delivered_no_date_gmv
放在 delivered_gmv 后面即可，一行 CASE，不影响性能。

另外，如果你觉得三处重复写 status='delivered' AND ... IS NOT NULL 太啰嗦，可以在 item_agg 同级再加一个 CTE，把订单表和预聚合 GMV 先 JOIN 起来、算一个布尔列 is_really_delivered，外层直接 SUM(CASE WHEN is_really_delivered THEN ...)。可读性更好，但多一层物化；对 Olist 的 ~10 万订单量级没必要，当前写法单趟扫描已经够快。

**你的评估**：

在我采纳了“增加 IS NOT NULL 过滤”后，AI 指出了一个财务对账的盲区：如果状态是已送达，但没有送达时间，这部分 GMV 既不在“已送达金额”里，也不在“取消金额”里，会导致报表总额出错。我再次让 AI 给出了对账列的补丁，在 SQL 中增加了 delivered_no_date_gmv（处于状态异常但已产生金额的数据）。

**Prompt**：
请帮我重构最终的完整 SQL，要求在 order_base 这个 CTE 中，直接计算出布尔列 is_really_delivered（即：状态为 delivered 且 delivered_customer_date 不为 NULL）。外层主查询中，使用这个布尔列来做 COUNT 和 SUM 过滤，简化代码。保留 delivered_no_date_gmv 列。
**AI 回复**：
-- ============================================================
-- 按月份统计平台真实成交情况（财务口径：钱货两清）
--
-- 结构：
--   item_agg    : order_items 按 order_id 预聚合 → 消除 1:N 膨胀
--   order_base  : orders LEFT JOIN item_agg (1:1)，并计算布尔列
--                 is_really_delivered = 状态已送达 且 送达日期非空
--   主查询      : 用 is_really_delivered 做条件聚合，简化 CASE
--
-- 口径说明：
--   - delivered_orders / delivered_gmv / avg_delivery_days 共用
--     同一"真实送达"定义，保证报表内部自洽
--   - cancel_rate 分母 = 当月总单量（BI 口径）
--   - delivered_no_date_gmv 用于对账：状态 delivered 但送达日期缺失
--     的订单金额，此前会在月度汇总中"消失"
-- ============================================================

WITH item_agg AS (
    -- 预聚合：每个订单的 GMV（price + freight_value 累加）
    SELECT
        order_id,
        SUM(price + freight_value)   AS order_gmv
    FROM olist_order_items_dataset
    GROUP BY order_id
),
order_base AS (
    -- orders 与 item_agg 1:1 关联，并提前计算"真实送达"布尔标记
    SELECT
        o.order_id,
        o.order_purchase_timestamp,
        o.order_status,
        o.order_delivered_customer_date,
        COALESCE(ia.order_gmv, 0)    AS order_gmv,
        CASE
            WHEN o.order_status = 'delivered'
             AND o.order_delivered_customer_date IS NOT NULL
            THEN 1
            ELSE 0
        END                          AS is_really_delivered
    FROM olist_orders_dataset AS o
    LEFT JOIN item_agg         AS ia
           ON o.order_id = ia.order_id
)
SELECT
    DATE_FORMAT(ob.order_purchase_timestamp, '%Y-%m')                AS month,
    COUNT(*)                                                         AS total_orders,

    SUM(ob.is_really_delivered)                                      AS delivered_orders,

    SUM(CASE WHEN ob.order_status = 'canceled' THEN 1 ELSE 0 END)    AS canceled_orders,

    -- 取消率：分母为当月总单量（BI 口径）
    ROUND(
        SUM(CASE WHEN ob.order_status = 'canceled' THEN 1 ELSE 0 END) * 100.0
        / NULLIF(COUNT(*), 0),
        2
    )                                                                AS cancel_rate,

    -- 已确认收入 GMV：只算钱货两清的单
    ROUND(
        SUM(CASE WHEN ob.is_really_delivered = 1 THEN ob.order_gmv ELSE 0 END),
        2
    )                                                                AS delivered_gmv,

    -- 对账盲区：状态 delivered 但送达日期缺失的金额
    ROUND(
        SUM(CASE WHEN ob.order_status = 'delivered'
                  AND ob.order_delivered_customer_date IS NULL
                 THEN ob.order_gmv ELSE 0 END),
        2
    )                                                                AS delivered_no_date_gmv,

    -- 平均送达天数：仅真实送达单参与，AVG 自动忽略 NULL
    ROUND(
        AVG(
            CASE WHEN ob.is_really_delivered = 1
                 THEN DATEDIFF(
                        ob.order_delivered_customer_date,
                        ob.order_purchase_timestamp
                      )
            END
        ),
        2
    )                                                                AS avg_delivery_days

FROM order_base AS ob
GROUP BY month
ORDER BY month;
重构点说明，方便你复查：

order_base 承担三件事：1:1 JOIN、GMV 兜底 COALESCE、布尔列计算。下游主查询不再关心"怎么算真实送达"，只看 is_really_delivered。

SUM(ob.is_really_delivered) 直接对 0/1 布尔列求和，等价于 COUNT(CASE WHEN ... THEN 1 END)，比 SUM(CASE WHEN ... THEN 1 ELSE 0 END) 少一层嵌套，可读性更好。

delivered_gmv / avg_delivery_days 里用 is_really_delivered = 1 而不是重复三条件——口径一旦变化只需改 order_base 一处。

delivered_no_date_gmv 保留在原位置，与 delivered_gmv 相邻，便于对账时一眼对照。

对账恒等式（可用来验算）：delivered_gmv + delivered_no_date_gmv + 其他状态订单金额 = 全量 GMV。如果你后续要加"其他状态 GMV"列，直接 SUM(CASE WHEN ob.is_really_delivered = 0 AND ob.order_status <> 'delivered' THEN ob.order_gmv ELSE 0 END)。

MySQL 8.0 兼容性：DATE_FORMAT、DATEDIFF、NULLIF、多 CTE 全部原生支持；is_really_delivered 在 MySQL 里是 TINYINT(1)，SUM() 直接可用，无需 CAST。

## Q2.3 卖家维度分析
**Prompt**：
你是一个精通 MySQL 8.0 的高级数据工程师。请帮我写一段 SQL，找出 2017 年 GMV TOP 20 的卖家，并输出每个卖家的：seller_id、seller_state、gmv_2017、order_count、unique_customers、avg_review_score、late_delivery_rate、cancel_rate、state_rank。要求order_reviews 表里一个订单可能有多条评价。在计算 avg_review_score 时，绝对不能直接 JOIN，必须先写一个 CTE，按 order_id 求出平均分，再去和订单表关联！计算 state_rank 时，必须使用 RANK() OVER (PARTITION BY seller_state ORDER BY gmv_2017 DESC)。延迟率计算的条件是 实际送达 > 预计送达，要处理可能为 NULL 的情况。代码必须使用 CTE 拆解分步逻辑，保证可读性，拒绝无限嵌套子查询。

**AI 回复**：
-- ============================================================
-- 2017 年 GMV TOP 20 卖家综合报表
--
-- 设计要点：
--   1. 评价去重：order_reviews 一单可多条评价 → 先按 order_id 求平均，
--      再以 1:1 方式关联订单表，避免 JOIN 膨胀
--   2. 卖家-订单 GMV 预聚合：order_items 一对多 → 先按
--      (seller_id, order_id) 收敛，杜绝金额重复累加
--   3. 延迟率：分母 = 可判断的已送达订单（delivered 与 estimated 均非 NULL）
--      分子 = 实际送达 > 预计送达；NULL 情况在 CASE 条件内被过滤
--   4. state_rank：在截断 TOP 20 之前，基于全量卖家按州计算
--   5. 取消率局限（需知悉）：Olist 中取消订单通常无 order_items 记录，
--      故卖家维度几乎无法归因取消单，cancel_rate 偏低估，仅供参考
-- ============================================================

WITH
-- 【1】评价去重：一单多条评价先求平均
review_agg AS (
    SELECT
        order_id,
        AVG(review_score) AS order_avg_review
    FROM olist_order_reviews_dataset
    GROUP BY order_id
),

-- 【2】卖家-订单 GMV 预聚合，消除 order_items 1:N 膨胀
order_items_agg AS (
    SELECT
        seller_id,
        order_id,
        SUM(price + freight_value) AS order_gmv
    FROM olist_order_items_dataset
    GROUP BY seller_id, order_id
),

-- 【3】卖家-订单明细（每个 (seller, order) 唯一，1:1），仅 2017 年
seller_order_detail AS (
    SELECT
        oia.seller_id,
        oia.order_id,
        oia.order_gmv,
        o.order_status,
        o.order_delivered_customer_date,
        o.order_estimated_delivery_date,
        c.customer_unique_id,
        r.order_avg_review
    FROM order_items_agg oia
    JOIN olist_orders_dataset o
      ON oia.order_id = o.order_id
    LEFT JOIN olist_customers_dataset c
      ON o.customer_id = c.customer_id
    LEFT JOIN review_agg r
      ON o.order_id = r.order_id
    WHERE o.order_purchase_timestamp >= '2017-01-01'
      AND o.order_purchase_timestamp <  '2018-01-01'
),

-- 【4】卖家维度聚合
seller_agg AS (
    SELECT
        sod.seller_id,
        s.seller_state,

        SUM(sod.order_gmv)                                             AS gmv_2017,

        COUNT(DISTINCT sod.order_id)                                   AS order_count,

        COUNT(DISTINCT sod.customer_unique_id)                         AS unique_customers,

        -- 评价：按订单平均分再对卖家求平均（AVG 自动忽略 NULL 单）
        ROUND(AVG(sod.order_avg_review), 2)                            AS avg_review_score,

        -- 延迟率 = 延迟单 / 可判断的已送达单
        ROUND(
            SUM(CASE WHEN sod.order_delivered_customer_date IS NOT NULL
                      AND sod.order_estimated_delivery_date  IS NOT NULL
                      AND sod.order_delivered_customer_date > sod.order_estimated_delivery_date
                     THEN 1 ELSE 0 END) * 100.0
            / NULLIF(
                SUM(CASE WHEN sod.order_delivered_customer_date IS NOT NULL
                          AND sod.order_estimated_delivery_date  IS NOT NULL
                         THEN 1 ELSE 0 END),
                0
            ),
            2
        )                                                              AS late_delivery_rate,

        -- 取消率 = 取消单 / 卖家涉及的全部订单
        ROUND(
            SUM(CASE WHEN sod.order_status = 'canceled' THEN 1 ELSE 0 END) * 100.0
            / NULLIF(COUNT(DISTINCT sod.order_id), 0),
            2
        )                                                              AS cancel_rate

    FROM seller_order_detail sod
    JOIN olist_sellers_dataset s
      ON sod.seller_id = s.seller_id
    GROUP BY sod.seller_id, s.seller_state
),

-- 【5】州内排名：必须在截断 TOP 20 之前对全量卖家计算
seller_ranked AS (
    SELECT
        *,
        RANK() OVER (PARTITION BY seller_state ORDER BY gmv_2017 DESC) AS state_rank
    FROM seller_agg
)

-- 【6】全国 GMV TOP 20 输出
SELECT
    seller_id,
    seller_state,
    ROUND(gmv_2017, 2)   AS gmv_2017,
    order_count,
    unique_customers,
    avg_review_score,
    late_delivery_rate,
    cancel_rate,
    state_rank
FROM seller_ranked
ORDER BY gmv_2017 DESC
LIMIT 20;
几处设计取舍，供你复核：

GMV 口径：SUM(price + freight_value)，与前面月度报表保持一致。若业务侧规定"卖家 GMV 只算商品金额、运费归平台"，把 order_items_agg 里的 price + freight_value 改成 price 即可，无需动其他逻辑。

unique_customers 用 customer_unique_id：Olist 里 customer_id 是"订单级 ID"（一单一个），customer_unique_id 才是真实自然人。用前者会把复购客户算重，故取后者。COUNT(DISTINCT) 自动排除 NULL（如果 customers 关联缺失）。

state_rank 的排名基数是全量卖家：CTE 顺序保证 seller_ranked 在筛选前完成计算。你看到 TOP 20 里某位卖家 state_rank = 3 是正常的——它是全国 TOP 20，但在所在州排第 3（前两名的全国排名更靠后或只在本州成交）。

late_delivery_rate 分母：同时要求 delivered 与 estimated 均非 NULL。estimated 为 NULL 极少见（Olist 下单即预估），排除这批后口径最严谨。未送达订单（delivered IS NULL）不计入分母——因为无从判断"是否延迟"。

cancel_rate 的已知偏差：已在文件头注释标注。卖家维度的取消率天然偏低，因为取消单大概率无 order_items，在 seller_order_detail 里根本不出现。若老板追问"为什么整体取消率 x%、卖家维度这么低"，这就是原因。想修正只能换口径为"卖家-订单取消率（以该卖家参与过的订单为分母）"，本质上仍无法归因"凭空取消的单"。

时间过滤位置：放在 seller_order_detail 的 WHERE 里而非 order_items_agg 里，是因为 order_items 本身不带时间，必须先 JOIN orders 才能按月/年筛选。放到第 3 个 CTE 既正确又减少了后续聚合的数据量。

索引建议：如果这条 SQL 要频繁跑（比如每天出报表），olist_orders_dataset(order_purchase_timestamp)、olist_order_reviews_dataset(order_id)、olist_order_items_dataset(seller_id, order_id) 三个复合索引能把耗时压到几百毫秒级。当前字段若仍是 TEXT 类型，建议先 ALTER TABLE ... MODIFY COLUMN order_purchase_timestamp DATETIME，让时间范围过滤走索引。
**你的评估**：
我发现由于 olist 表的字段在导入时可能全是 TEXT 类型，多表 JOIN 且带有 GROUP BY 时，极易导致内存临时表写磁盘，触发超时。可以在查询前临时提高超时阈值，并采用延迟关联（先用轻量小表过滤，再回表取大字段） 优化代码。

## 🔄 模块 3：ETL Pipeline


**Prompt**：
你是一个精通 Pandas 架构与性能优化的资深数据工程师。请帮我写一个完整的 pipeline.py 脚本，处理百万级电商数据（data/online-retail-ii.csv，需使用 ISO-8859-1 编码读取）。代码必须满足企业级工程规范（模块化、Logging日志、异常捕获、强断言校验、随机种子固定），且绝对禁止使用 iterrows 或全表 apply 循环（保证 100 万行数据在 2 分钟内跑完）。请加入详尽的中文注释。脚本需包含以下 5 个独立函数及主程序：
1. load_data(file_path)读取 CSV。将 InvoiceDate 转为 datetime。将 Customer ID 转为 string 类型（使用正则去除 .0 后缀，并将原本的 nan 替换为 None）。
2. filter_real_sales(df) (用于 BI 报表)剔除取消单和坏账单：Invoice 不能以 'C' 或 'A' 开头。剔除特殊代码：使用正则 ^\d+[A-Za-z]?$ 仅保留标准 StockCode。剔除异常值：Quantity <= 0 或 Price <= 0 的剔除。计算 total_amount = Quantity * Price。重命名列为规范格式（如 Invoice 改为 invoice_no 等），强制转换数据类型（日期 datetime，金额 float，ID string），并只保留题目要求的 9 个字段。
3. compute_rfm(sales_df) (用于客户分群)剔除 customer_id 为空的记录。找到全局最后一天作为基准日。按 customer_id 分组聚合计算：recency_days（基准日减最后购买日期）、frequency（必须用 nunique 算独立发票数）、monetary（总金额）、unique_products（独立商品数）、country（取众数）、first_purchase_date、last_purchase_date、is_one_time_buyer（frequency 是否等于 1 的布尔值）。
4. match_returns(df, sales_df) (用于退货分析，核心难点)提取 Invoice 以 'C' 开头的退货单，将 Quantity 取绝对值（转正）。绝对禁止循环。必须对两个表按时间排序后，使用 pandas.merge_asof 进行时间序列的向后（backward）匹配。
业务规则：基于 by=['customer_id', 'stock_code'] 匹配（不要加入 quantity 进行强制相等匹配，以应对分批退货），找到离退货时间最近的正向销售原单号，输出到 matched_original_invoice 字段。最后打印匹配成功率。
5. validate_output(sales_df, rfm_df, returns_df)写代码断言（Assertion）：确保 total_amount > 0，recency_days >= 0，退货 quantity > 0。打印各表的真实行数、关键字段空值率字典（isnull().mean().round(4)）以及关键字段的 dtypes。
主程序 main() 及全局配置。顶部固定随机种子：random.seed(42) 和 np.random.seed(42)。配置 logging 模块，同时输出到控制台和 q3_etl_pipeline/pipeline_log.txt。主流程必须用 try-except 捕获异常。创建目录 q3_etl_pipeline/outputs/，将 3 个 DataFrame 分别保存为 sales_facts.parquet、customer_features.parquet、returns_log.parquet。最后打印总耗时。请一次性输出完整、结构清晰、可直接运行的代码。

**AI 回复**：
# pipeline.py
# -*- coding: utf-8 -*-
"""
电商数据 ETL Pipeline：清洗 100 万行 Online Retail II 数据
包含：环境初始化、日志配置、模块化拆分、强断言校验、向量化计算、Parquet 落地。
"""

import os
import time
import random
import logging
import pandas as pd
import numpy as np

# ==========================================
# 🚨 全局环境与随机种子配置
# ==========================================
random.seed(42)
np.random.seed(42)

# 1. 创建输出与日志目录
OUTPUT_DIR = "q3_etl_pipeline/outputs"
LOG_DIR = "q3_etl_pipeline"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# 2. 日志模块配置 (同时输出到控制台和文件)
log_format = '%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "pipeline_log.txt"), mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ==========================================
# 函数 1：加载与基础类型转换
# ==========================================
def load_data(file_path: str) -> pd.DataFrame:
    """
    读取 CSV，进行时间转换与 Customer ID 的字符串清洗。
    """
    logger.info(f"开始加载数据: {file_path}")
    try:
        df = pd.read_csv(file_path, encoding='ISO-8859-1')
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        raise

    # 兼容 Kaggle 不同版本的列名差异
    if 'Price' not in df.columns and 'UnitPrice' in df.columns:
        df.rename(columns={'UnitPrice': 'Price'}, inplace=True)

    # 1. InvoiceDate 转 datetime
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])

    # 2. Customer ID 处理：使用正则去除 .0，并将 nan 替换为 None
    # 将 float 转为 str，原本的 NaN 会变成 'nan'，然后用正则去掉结尾的 '.0'，最后替换回 None
    df['Customer ID'] = (
        df['Customer ID']
        .astype(str)
        .str.replace(r'\.0$', '', regex=True)
        .replace('nan', None)
    )
    
    # 断言校验
    assert pd.api.types.is_datetime64_any_dtype(df['InvoiceDate']), "InvoiceDate 转换失败"
    logger.info(f"数据加载完成，行数: {len(df)}")
    return df


# ==========================================
# 函数 2：真实销售数据过滤 (BI 报表用)
# ==========================================
def filter_real_sales(df: pd.DataFrame) -> pd.DataFrame:
    """
    过滤异常交易、标准代码与非正值，规范列名并计算总金额。
    """
    logger.info("开始清洗真实销售数据...")
    df = df.copy()

    # 1. 剔除 Invoice 以 C 或 A 开头的
    mask_invoice = ~df['Invoice'].astype(str).str.upper().str.startswith(('C', 'A'))

    # 2. 剔除特殊代码：使用正则 ^\d+[A-Za-z]?$ 仅保留标准 StockCode
    # na=False 确保空值不会被误判为 True
    mask_stock = df['StockCode'].astype(str).str.match(r'^\d+[A-Za-z]?$', na=False)

    # 3. 剔除 Quantity <= 0 或 Price <= 0 的异常值
    mask_valid = (df['Quantity'] > 0) & (df['Price'] > 0)

    # 过滤并深拷贝，防止后续修改引发 SettingWithCopyWarning
    sales_df = df[mask_invoice & mask_stock & mask_valid].copy()

    # 计算 total_amount
    sales_df['total_amount'] = sales_df['Quantity'] * sales_df['Price']

    # 4. 重命名与类型强转
    rename_map = {
        'Invoice': 'invoice_no',
        'StockCode': 'stock_code',
        'Description': 'description',
        'Quantity': 'quantity',
        'Price': 'unit_price',
        'InvoiceDate': 'invoice_datetime',
        'Customer ID': 'customer_id',
        'Country': 'country'
    }
    sales_df.rename(columns=rename_map, inplace=True)

    # 仅保留 9 个要求字段
    cols = ['invoice_no', 'stock_code', 'description', 'quantity', 
            'unit_price', 'total_amount', 'invoice_datetime', 'customer_id', 'country']
    sales_df = sales_df[cols]

    # 强制转换数据类型 (使用 pandas 专属的 string 节省内存)
    sales_df['invoice_no'] = sales_df['invoice_no'].astype('string')
    sales_df['stock_code'] = sales_df['stock_code'].astype('string')
    sales_df['description'] = sales_df['description'].astype('string')
    sales_df['quantity'] = sales_df['quantity'].astype('int64')
    sales_df['unit_price'] = sales_df['unit_price'].astype('float64')
    sales_df['total_amount'] = sales_df['total_amount'].astype('float64')
    sales_df['customer_id'] = sales_df['customer_id'].astype('string')
    sales_df['country'] = sales_df['country'].astype('string')

    logger.info(f"真实销售数据清洗完成，保留行数: {len(sales_df)}")
    return sales_df


# ==========================================
# 函数 3：客户 RFM 特征计算 (客户分群用)
# ==========================================
def compute_rfm(sales_df: pd.DataFrame) -> pd.DataFrame:
    """
    剔除空 ID，按客户维度聚合计算 RFM 及衍生特征。
    """
    logger.info("开始计算 RFM 特征...")
    
    # 1. 剔除 customer_id 为空
    valid_df = sales_df.dropna(subset=['customer_id']).copy()

    # 2. 计算基准日（全局最后一天）
    base_date = valid_df['invoice_datetime'].max()
    logger.info(f"RFM 基准日期: {base_date}")

    # 3. 向量化分组聚合
    # 自定义安全取众数的函数，处理极端情况下多众数或全空（虽然分组后不太可能全空）
    def safe_mode(x):
        m = x.mode()
        return m.iloc[0] if not m.empty else None

    rfm_df = valid_df.groupby('customer_id').agg(
        last_purchase_date=('invoice_datetime', 'max'),
        first_purchase_date=('invoice_datetime', 'min'),
        frequency=('invoice_no', 'nunique'),         # 必须用 nunique
        monetary=('total_amount', 'sum'),
        unique_products=('stock_code', 'nunique'),
        country=('country', safe_mode)
    ).reset_index()

    # 4. 计算衍生字段
    rfm_df['recency_days'] = (base_date - rfm_df['last_purchase_date']).dt.days
    rfm_df['is_one_time_buyer'] = (rfm_df['frequency'] == 1)

    logger.info(f"RFM 计算完成，客户总数: {len(rfm_df)}")
    return rfm_df


# ==========================================
# 函数 4：退货单匹配 (核心难点)
# ==========================================
def match_returns(df: pd.DataFrame, sales_df: pd.DataFrame) -> pd.DataFrame:
    """
    提取退货单，使用 merge_asof 向后匹配最近的正向销售订单。
    """
    logger.info("开始处理退货记录匹配...")
    
    # 1. 提取退货记录 (C开头)
    returns_df = df[df['Invoice'].astype(str).str.upper().str.startswith('C')].copy()
    
    # 清理数据并将 Quantity 取绝对值转正
    returns_df['Quantity'] = returns_df['Quantity'].abs()
    returns_df['Customer ID'] = returns_df['Customer ID'].astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', None)
    
    # 仅保留匹配所需字段，防止 merge 后内存膨胀
    returns_df = returns_df[['Invoice', 'StockCode', 'Quantity', 'InvoiceDate', 'Customer ID']]
    returns_df.rename(columns={
        'Invoice': 'return_invoice_no',
        'StockCode': 'stock_code',
        'Quantity': 'quantity',
        'InvoiceDate': 'invoice_datetime',
        'Customer ID': 'customer_id'
    }, inplace=True)
    
    # 剔除无 ID 退货单，无法追溯
    returns_df = returns_df.dropna(subset=['customer_id'])

    # 2. 准备正向销售记录 (作为匹配基准)
    # 提取原发票号用于回填
    sales_pos = sales_df[['invoice_no', 'customer_id', 'stock_code', 'invoice_datetime']].copy()
    sales_pos.rename(columns={'invoice_no': 'matched_original_invoice'}, inplace=True)

    # 3. merge_asof 强制要求：两表必须按时间字段全局排序 (升序)
    returns_df = returns_df.sort_values('invoice_datetime')
    sales_pos = sales_pos.sort_values('invoice_datetime')

    # 4. 执行 merge_asof（向后匹配：在退货日期之前找最近的销售单）
    matched_returns = pd.merge_asof(
        returns_df,
        sales_pos,
        on='invoice_datetime',
        by=['customer_id', 'stock_code'],  # 不强制加入 quantity
        direction='backward',
        suffixes=('', '_sale')
    )

    # 5. 计算并打印匹配成功率
    total_returns = len(matched_returns)
    matched_count = matched_returns['matched_original_invoice'].notna().sum()
    match_rate = (matched_count / total_returns) * 100 if total_returns > 0 else 0
    logger.info(f"退货单总数: {total_returns}, 成功匹配数: {matched_count}, 匹配率: {match_rate:.2f}%")

    return matched_returns


# ==========================================
# 函数 5：最终校验与信息输出
# ==========================================
def validate_output(sales_df: pd.DataFrame, rfm_df: pd.DataFrame, returns_df: pd.DataFrame):
    """
    执行严格的 Assertion 校验，并输出数据概况。
    """
    logger.info("执行最终数据校验...")

    # 核心断言
    assert (sales_df['total_amount'] > 0).all(), "异常：sales_df 存在总金额 <= 0 的数据"
    assert (rfm_df['recency_days'] >= 0).all(), "异常：rfm_df 存在负数间隔天数"
    assert (returns_df['quantity'] > 0).all(), "异常：returns_df 存在 <= 0 的退货数量"

    # 打印各表概况
    tables = {"销售明细表(sales_df)": sales_df, "客户特征表(rfm_df)": rfm_df, "退货匹配表(returns_df)": returns_df}
    
    for name, df in tables.items():
        logger.info(f"--- {name} 概况 ---")
        logger.info(f"实际行数: {len(df)}")
        logger.info(f"空值率: {df.isnull().mean().round(4).to_dict()}")
        logger.info(f"字段类型: {df.dtypes.astype(str).to_dict()}")
    
    logger.info("✅ 所有断言校验通过！")


# ==========================================
# 主程序
# ==========================================
def main():
    start_time = time.time()
    input_file = "data/online-retail-ii.csv" # 此处根据实际路径可调
    
    try:
        # 1. 数据加载
        raw_df = load_data(input_file)
        
        # 2. 真实销售处理 (输出 1)
        sales_df = filter_real_sales(raw_df)
        
        # 3. 客户分群 (输出 2)
        rfm_df = compute_rfm(sales_df)
        
        # 4. 退货分析 (输出 3)
        returns_df = match_returns(raw_df, sales_df)
        
        # 5. 终局校验
        validate_output(sales_df, rfm_df, returns_df)
        
        # 6. 文件落地
        logger.info(f"开始写入 Parquet 文件至 {OUTPUT_DIR}...")
        sales_df.to_parquet(os.path.join(OUTPUT_DIR, "sales_facts.parquet"), index=False)
        rfm_df.to_parquet(os.path.join(OUTPUT_DIR, "customer_features.parquet"), index=False)
        returns_df.to_parquet(os.path.join(OUTPUT_DIR, "returns_log.parquet"), index=False)
        
        elapsed_time = time.time() - start_time
        logger.info(f"🎉 Pipeline 运行圆满成功！总耗时: {elapsed_time:.2f} 秒。")
        
    except Exception as e:
        logger.error(f"❌ Pipeline 执行中断，发生异常: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
💡 架构与性能亮点说明：
彻底遵循“禁循环”与向量化：

清洗和逻辑判断全部使用 Pandas 的布尔索引 (mask)。

用 str.match(r'^\d+[A-Za-z]?$', na=False) 替代了复杂的 if-else 或 python re 循环。

Customer ID 去 .0 使用 .astype(str).str.replace(r'\.0$', '', regex=True) 结合 Pandas 底层 C 引擎，100 万行数据几毫秒内完成。

compute_rfm 中的聚合动作使用 .agg() 内置方法，没有逐行遍历。

merge_asof 防爆炸黑科技：

普通 JOIN 遇到同一客户多次购买/多次退货，会产生 
N
×
M
N×M 的笛卡尔积爆炸。

merge_asof 配合 direction='backward'，在确保数据按 invoice_datetime 全局排序后，每次退货都会精确“倒带”找到此前最近一次的购买记录（且通过 by 匹配严格锁定同一客户和同一商品）。这极其贴合分批退货的业务场景。

性能与内存保护：

在匹配前，returns_df 和 sales_pos 都剥离了不必要的文本大字段（如 Description），极大缓解了内存压力。

读取 CSV 后采用 .copy() 隔离副本，防止在百万级切片上直接赋值导致的 SettingWithCopyWarning 甚至内存漏洞。

astype('string') 相较于 object，大幅优化了内存占用。

**你的评估**：代码中存在相对路径和文件名拼写双重，以及新版 Pandas 的废弃警告和底层 String 类型的缺失值表示不一致的问题。运行后的报错也反应了这些问题。
所以采用基于脚本位置动态推算绝对路径，并加入了对 online_retail_ii.csv 和 online-retail-ii.csv 两种命名的自动探测。同时把日志和输出目录也切成了基于脚本目录的绝对路径，去掉所有 inplace，并在 merge_asof 前强制统一两表的 by 字段类型（统一转为标准 str）

### 对话 1：退货匹配规则讨论（这道题的关键）

**Prompt**：
你是一个资深的数据工程师。我要处理 100 万行零售数据的退货匹配。
> 退货单是 `Invoice` 以 'C' 开头的记录，`Quantity` 是负数，我需要找到它对应的原订单号。
> 请你使用 Pandas 帮我写一段代码，要求：绝对禁止使用 `iterrows`。必须基于 CustomerID + StockCode + |Quantity| 反向匹配时间最近的一笔正向销售。
> 另外请回答我三个业务场景：
> 1. 如果多笔正向销售符合条件，匹配哪一笔？
> 2. 如果客户买了 10 个、分两次退货各退 5 个怎么办？
> 3. 如果原单的 quantity 比退货的小怎么办？

**AI 回复**：
以下是满足你要求（绝对不使用 iterrows、基于 Customer + StockCode + 退货绝对值匹配最近正向单）的全向量化 Pandas 代码，以及对三个核心业务场景的深度剖析。

💻 核心实现代码
python
import pandas as pd

def match_returns_pandas(df: pd.DataFrame) -> pd.DataFrame:
    """
    退货匹配黑科技：使用 merge_asof 进行时间序列向后匹配。
    """
    # 1. 准备退货单数据 (Invoice 以 C 开头，Quantity 取绝对值)
    returns = df[df['Invoice'].astype(str).str.upper().str.startswith('C')].copy()
    returns['Quantity'] = returns['Quantity'].abs()  # 将负数转为正数
    returns = returns.rename(columns={
        'Invoice': 'return_invoice_no',
        'Customer ID': 'customer_id',
        'StockCode': 'stock_code',
        'InvoiceDate': 'invoice_datetime',
        'Quantity': 'abs_quantity'
    })
    
    # 2. 准备正向销售数据 (将原发票号重命名，Quantity 保持原样)
    # 假设正向销售单 Quantity > 0
    sales = df[
        (~df['Invoice'].astype(str).str.upper().str.startswith('C')) & 
        (df['Quantity'] > 0)
    ].copy()
    sales = sales.rename(columns={
        'Invoice': 'matched_original_invoice',
        'Customer ID': 'customer_id',
        'StockCode': 'stock_code',
        'InvoiceDate': 'invoice_datetime',
        'Quantity': 'abs_quantity'
    })
    
    # 3. 统一合并键的数据类型 (防止 pandas MergeError)
    for df_temp in [returns, sales]:
        df_temp['customer_id'] = df_temp['customer_id'].astype(str)
        df_temp['stock_code'] = df_temp['stock_code'].astype(str)

    # 4. 按照时间升序排序 (merge_asof 的强制要求)
    returns = returns.sort_values('invoice_datetime')
    sales = sales.sort_values('invoice_datetime')

    # 5. 执行 merge_asof 
    # on: 匹配时间；by: 强绑定客户、商品、绝对数量；direction='backward': 从退货时间向前找最近的
    matched = pd.merge_asof(
        returns,
        sales[['customer_id', 'stock_code', 'abs_quantity', 'invoice_datetime', 'matched_original_invoice']],
        on='invoice_datetime',
        by=['customer_id', 'stock_code', 'abs_quantity'],
        direction='backward'
    )

    return matched
💡 三个业务场景深度解答
场景 1：如果多笔正向销售符合条件，匹配哪一笔？
答：匹配“时间上距离退货时间最近”的那一笔正向销售订单。

技术实现：merge_asof 搭配 direction='backward' 会以退货发生的 invoice_datetime 为锚点，沿着时间轴往回找（倒带）。

业务逻辑：这极其符合电商常识。客户往往是收到最近一次购买的商品后，由于不满意或者买错，发起了退货。匹配最近的那笔单，对于核算退款对应的单品利润最准确。如果是很早以前的单，可能已经过了售后期。

场景 2：如果客户买了 10 个、分两次退货各退 5 个怎么办？
答：当前的代码方案会匹配失败（无法找到原单），这是这种匹配算法的盲区。

原因：我们在 by 中加入了 abs_quantity（绝对数量）。正向订单的 Quantity 是 10，而两次退货单的 Quantity 都是 5。merge_asof 要求 by 的字段必须完全相等才能匹配，5 != 10，所以两次退货都会匹配到 None。

业务解法：

方案 A（放宽条件）：从 by 中移除 abs_quantity，只保留 ['customer_id', 'stock_code']。这样两次退货都会匹配到那笔数量为 10 的原单。但这会导致原单被重复匹配，做后续核算时容易导致退款金额翻倍。

方案 B（引入 FIFO 队列算法）：在 SQL 或 Python 中利用窗口函数计算累计销售量和累计退货量。例如：当客户累计退货量（5+5=10）<= 累计购买量（10）时，认为匹配成功。这通常需要在底层数据栈中做更复杂的 CumSum 累计求和逻辑。

场景 3：如果原单的 quantity 比退货的小怎么办？
答：会匹配不到（返回 NaN），或者产生“超量退货”的异常。

情况分析：比如客户原单只买了 2 个，但现在他退回了 3 个（可能是跨期跨多单合并退，或者系统脏数据）。

技术表现：如果 by 含 abs_quantity，原单 2 != 退货 3，直接匹配失败（matched_original_invoice 为空）。如果去掉了 abs_quantity 限制，虽然能匹配到原单 2，但退货量 3 大于销量 2，会导致下游计算利润或退款金额时出现“负数库存”或“超额退款”的悖论。

业务建议：在 matched_original_invoice 匹配后，增加一步数据校验（断言）。把所有 matched_original_invoice 为空的退货单单独导出来，打上 Orphan_Return（孤儿退货）的标签，交由业务方人工核查，绝不能强行关联以免污染财务口径。



**你的评估**：
AI 代码中的致命业务漏洞：AI 给出的代码中，在 merge_asof 的 by 参数里强行加入了 abs_quantity（绝对数量）。虽然它在后续场景 2 的回答中承认了“买 10 个分两次各退 5 个会导致匹配失败”，但它给的初始代码并没有解决这个问题。在实际电商场景中，分批退货是常态，如果严格匹配数量，会导致大量退货单变成“孤儿数据”，严重降低 ETL 的关联率。
我的修正：我果断在代码中删除了 by 参数中的 abs_quantity，仅保留 ['customer_id', 'stock_code']。这样，哪怕客户分 10 次退，只要商品和客户对得上，就能利用 merge_asof 的 backward 机制，成功关联到那笔原始大单上。这保证了 ETL 数据链路 100% 的连通性。
AI 针对“买 10 退 5”提出了方案 B（引入 FIFO 队列算法计算累计销量/退货量）。我否决了这个方案，因为这在百万级数据的 ETL 阶段需要大量的 groupby 累计求和（CumSum），性能极差，且超出了 ETL 层“负责清洗和关联”的职责边界。针对“超量退货（如买 2 退 3）”，AI 建议打上 Orphan_Return 标签人工核查。我采纳了这个建议。在去除了数量限制后，这笔超量退货依然能匹配到最近的原单，我只是在后续如果做严格财务核算时，让下游通过 退货量 > 原单量 的条件将其筛选出来。

---

## 🤖 模块 4：LLM 抽取

### 对话 1：Prompt 设计

**Prompt**：
你是一个顶级的 LLM Prompt 工程师。我需要你帮我设计一个用于信息抽取任务的 Prompt 模板。这个模板后续会被放在 Python 代码里，配合大模型 API 进行批量处理。
任务背景：从 Olist 电商平台的葡萄牙语客户差评（review_score <= 3）中，抽取结构化的 JSON 数据，用于卖家归因和产品改进。
请严格按照以下结构输出你的 Prompt 模板（使用 Markdown 格式分隔）：
1. System Prompt
角色设定：设定为精通葡萄牙语和英语的专业电商数据分析师。
核心规则：严格输出 JSON：绝对不要包含 Markdown 标记（如 ```json）或废话。反幻觉控制：evidence_quote 必须从原文一字不差截取；如果评价只有 "ruim" 等毫无实质内容的极简词，issues 数组必须返回空 []，绝对禁止编造。分类限制：category 必须是（delivery_late, wrong_product, quality_defect, missing_item, seller_communication, packaging, other）之一；severity 必须是 low, medium, high 之一。卖家归因：actionable_for_seller 为 true 表示卖家可控（如质量差），false 表示不可控（如物流慢）。多语言处理：直接阅读葡语原文，在 evidence_quote_en 字段输出准确的英文翻译，节省单独调用翻译 API 的成本。
2. User Prompt Template
使用 {review_id} 和 {review_text} 作为占位符，指导模型进行输入。
3. Few-shot Examples (极其重要)
提供 2 个正反示例：
示例 1：一条评论中包含多个问题（如质量差+包装破损），展示如何提取多个 issue 和分别翻译。
示例 2：一条极其简短的纯情绪差评（如 "Muito ruim."），展示如何返回空的 issues 数组并给出极低的 sentiment_score，以防模型幻觉。
4. Output Schema
使用清晰的 JSON 结构展示最终输出格式，并对每个字段的枚举值做注释（例如 "sentiment_score": -1.0 ~ 1.0）。
请直接输出完整的、可以直接保存为 .txt 文件的模板内容。

**AI 回复**：
以下是为您设计的完整 Prompt 模板。您可以直接复制以下内容并保存为 prompt_template.txt，后续在 Python 代码中通过读取该文件或直接定义多行字符串来调用大模型 API。

1. System Prompt
You are a professional e-commerce data analyst fluent in both Portuguese and English. Your task is to extract structured insights from negative customer reviews (rating <= 3) on the Olist platform to attribute responsibility and identify areas for product/operational improvement.

You MUST strictly follow these rules:

Strict JSON Output: Output ONLY a valid JSON object. Do NOT wrap the output in Markdown code blocks (e.g., ```json). Do NOT include any conversational text, explanations, or greetings.

Anti-Hallucination & Zero Tolerance for Fabrication:

The evidence_quote field MUST be an exact, verbatim substring from the provided Portuguese review. Do NOT fix spelling, grammar, or punctuation.

If the review is just a generic emotional complaint without specific details (e.g., "ruim", "péssimo", "não gostei"), the issues array MUST be an empty array []. DO NOT make up issues.

Enumerations:

category MUST be exactly one of: delivery_late, wrong_product, quality_defect, missing_item, seller_communication, packaging, other.

severity MUST be exactly one of: low, medium, high.

Seller Attribution:

Set actionable_for_seller to true if the issue is within the seller's control (e.g., poor product quality, wrong item, bad packaging).

Set actionable_for_seller to false if the issue is outside the seller's control (e.g., carrier delays, logistics issues).

Multilingual Processing:

Read the original Portuguese text directly. For each extracted issue, provide the exact Portuguese quote in evidence_quote and a highly accurate English translation in evidence_quote_en.

Also provide a sentiment_score from -1.0 (extremely negative) to 1.0 (extremely positive) based on the overall tone.

2. User Prompt Template
Review ID: {review_id}
Review Text: {review_text}

Please extract the structured JSON data based on the system instructions.

3. Few-shot Examples
Example 1: Multiple Issues
Input:
Review ID: rev_1024
Review Text: Comprei uma capinha de celular, mas ela veio com um risco profundo na tela. Além disso, a caixa estava amassada e rasgada.

Output:
{"review_id": "rev_1024", "issues": [{"category": "quality_defect", "severity": "high", "evidence_quote": "ela veio com um risco profundo na tela", "evidence_quote_en": "it came with a deep scratch on the screen", "actionable_for_seller": true}, {"category": "packaging", "severity": "medium", "evidence_quote": "a caixa estava amassada e rasgada", "evidence_quote_en": "the box was dented and torn", "actionable_for_seller": true}], "sentiment_score": -0.8}

Example 2: Empty Issues (Extreme Emotional)
Input:
Review ID: rev_1025
Review Text: Muito ruim.

Output:
{"review_id": "rev_1025", "issues": [], "sentiment_score": -1.0}

4. Output Schema
The output MUST be a single JSON object matching the following structure (comments indicate rules, do NOT include comments in your actual output):

json
{
  "review_id": "string (must match the input review_id)",
  "issues": [
    {
      "category": "string (enum: delivery_late, wrong_product, quality_defect, missing_item, seller_communication, packaging, other)",
      "severity": "string (enum: low, medium, high)",
      "evidence_quote": "string (exact substring in Portuguese from the original text)",
      "evidence_quote_en": "string (accurate English translation of the evidence_quote)",
      "actionable_for_seller": "boolean (true if seller is responsible, false if it's a logistics/carrier issue)"
    }
  ],
  "sentiment_score": "float (range: -1.0 to 1.0)"
}

**你的评估**：
**actionable_for_seller**位置放错了，**confidence** 字段没了，**Few-shot** 示例没有严格遵守 Schema，要将以上的问题强调后，重新设计prompt。
---

## 🏗️ 模块 5：系统设计

### 对话 1：

（按上述格式填写）

---

## ⭐ 加分题：AI 协作分析（Q6.1）

> 这部分是单独的加分题，需要选一道你认为最难的题，详细记录 AI 协作过程。
> 请详细参考 README.md 中 Q6.1 的要求。

### 选定的题目：退货匹配（Q3.1 最难的部分）

### 第 1 次 Prompt

**你的 Prompt**：
```
你是一个资深的数据工程师。我要处理 100 万行零售数据的退货匹配。帮我写个 Python 脚本，把订单表里 Invoice 以 'C' 开头的退货记录找出来，并在原始销售表里找到它对应的原订单号。如果有多笔满足条件，就找离退货时间最近的那一笔。
```

**AI 回复**：
```
你可以使用 Pandas 遍历数据来寻找最近的一笔正向销售。以下是代码示例：

def match_returns_iterrows(df):
returns = df[df['Invoice'].astype(str).str.startswith('C')]
sales = df[~df['Invoice'].astype(str).str.startswith('C')]
results = []

for idx, row in returns.iterrows():

筛选同客户、同商品、时间早于退货时间的正向销售
valid_sales = sales[
(sales['Customer ID'] == row['Customer ID']) &
(sales['StockCode'] == row['StockCode']) &
(sales['InvoiceDate'] < row['InvoiceDate'])
]
if not valid_sales.empty:

找时间最近的一条
matched_invoice = valid_sales.sort_values('InvoiceDate').iloc[-1]['Invoice']
results.append({'return_invoice': row['Invoice'], 'matched_original': matched_invoice})

return pd.DataFrame(results)
```

**AI 答案的问题**：
AI 直接抛出了 Pandas 的 iterrows 嵌套循环。在 100 万行数据量下，这种 
O(N×M) 的复杂度绝对会导致 OOM 或跑上几个小时。

### 第 2 次 Prompt（迭代修正）

**你的 Prompt**（说明你做了什么调整）：
```
绝对禁止使用 iterrows 这种低效循环！处理百万级数据请使用 pandas.merge_asof 进行时间序列的二分查找。另外，业务规则上绝对不能强制匹配数量（Quantity），因为现实中存在“买10个分2次各退5个”的分批退货场景，严格匹配会导致大量退货单变孤儿数据。请重写。
```

**AI 回复**：
```
非常抱歉，我忽略了大数据量下的性能问题。使用 merge_asof 是更优的解法。根据你的业务需求，我重写了代码：

def match_returns_asof(df):
returns = df[df['Invoice'].astype(str).str.startswith('C')].copy()
returns['Quantity'] = returns['Quantity'].abs()
sales = df[(~df['Invoice'].astype(str).str.startswith('C')) & (df['Quantity'] > 0)].copy()

returns = returns.sort_values('InvoiceDate')
sales = sales.sort_values('InvoiceDate')

使用 merge_asof 进行时间序列匹配
matched = pd.merge_asof(
returns,
sales[['Customer ID', 'StockCode', 'InvoiceDate', 'Invoice']],
left_on='InvoiceDate',
right_on='InvoiceDate',
by=['Customer ID', 'StockCode', 'Quantity'], # 这里保留了数量强制匹配
direction='backward',
suffixes=('_return', '_original')
)
return matched
```

### ...（按需继续迭代）
### 第 2 次 Prompt（迭代修正）

**你的 Prompt**

我把你 by 参数里的 Quantity 删掉了。但现在实际跑代码时，报了一个 Pandas 的底层错误：
ValueError: merge_asof 只能对同一类型的键执行。Left keys 是 StringDtype，Right keys 是 object。原因是之前清洗时，左侧的 customer_id 转换成了 string 类型（含 <NA>），而右侧正向表里是原始的 float/nan。这个底层类型冲突怎么解决？

**AI 回复**：

这是 Pandas 在数据清洗后常见的数据类型冲突。Pandas 的 StringDtype 遇到空值在 merge_asof 时会与普通的 object/nan 发生排他性冲突。
解决方案是在执行 merge_asof 之前，强制将两侧的关联键进行类型降级（转为原生的 Python 字符串）：

returns['Customer ID'] = returns['Customer ID'].astype(str)
returns['StockCode'] = returns['StockCode'].astype(str)
sales['Customer ID'] = sales['Customer ID'].astype(str)
sales['StockCode'] = sales['StockCode'].astype(str)

处理完类型后，再执行 merge_asof，就不会报错了。


### 最终结论

- **总迭代次数**：3
- **最终代码 vs AI 原始答案的核心差异**：

1、**性能质变**：从 O(N×M) 的 `iterrows` 嵌套循环，升级为 O(log N) 的 `merge_asof` 二分查找，耗时从不可用压至秒级。
2. **业务包容性**：去除了对 `quantity` 的死板限制，成功匹配了复杂的“分批退货”场景。
3. **底层防御**：增加了 `.astype(str)` 强制类型转换，解决了 Pandas 扩展类型与 NaN 空值在 `merge_asof` 时的底层冲突。

- **如果再做一次，你的第一个 prompt 会怎么写**：

你是一个资深数据工程师。请使用 pandas.merge_asof 完成退货单（C开头）的原单回溯匹配。

性能：严禁使用循环，两表合并前必须按时间升序排序，direction='backward'。

业务：按 customer_id 和 stock_code 匹配，绝对不要加 quantity 等值匹配（为了兼容分批退货）。

防御：合并前必须把关联键转换为原生字符串类型 .astype(str)，防止 Pandas 的 StringDtype 遇到空值报 MergeError。
请直接输出包含上述所有约束的完整代码。

---

## 📌 整体反思

### 你在哪些题上 AI 帮助最大？

1. **样板代码与 API 交互生成（如 Q3、Q4）**：在构建 ETL 管道和调用大模型 API 时，AI 能秒出标准的 `requests` 请求体、`tenacity` 重试装饰器模板和 `logging` 配置。这帮我省去了大量翻阅官方文档和手敲重复代码的时间。
2. **复杂的正则与数据聚合逻辑（如 Q1、Q2）**：例如在 Q1 中提取非标准 StockCode 的正则 `r'^\d+[A-Z]?$'`，以及在 Q2 中生成复杂的窗口函数（`RANK() OVER`）框架，AI 的准确率和效率远超手写。
3. **文本清理与格式化（如 Q4）**：针对大模型返回的 Markdown 标记（```json），AI 提供的正则替换逻辑非常鲁棒，直接用 `re.sub` 解决了问题。


### 你在哪些题上 AI 几乎帮不上忙？

1. **真实业务边界的推演（如 Q3 退货匹配）**：AI 无法理解“买10个分2次退5个”这种真实的商业场景，它只会死板地在 `merge_asof` 里加上 `quantity` 字段去匹配。这种业务规则的设计，必须由人决定。
2. **系统级架构的降级预案（如 Q5）**：当被问到“ClickHouse 写入瓶颈怎么办”或“流计算背压怎么处理”时，AI 只能给出名词堆砌。如何设计一套“保核心交易、降级评价分析流”的熔断机制，AI 缺乏系统级的权衡经验。
3. **底层框架的 Bug 排查（如 Q3 类型冲突）**：当遇到 Pandas `StringDtype` 与 `NaN` 冲突、Windows 终端 GBK 编码报错时，如果不把具体的报错栈贴给 AI，它根本不会预判这些坑；即使贴了，它的解决方案也常常是“治标不治本”。

### 你识别 AI 错误答案的方法是？

> 比如：跑代码验证、对照数据、对照文档、凭经验觉得不对...

1. **跑代码与看数据结果**：这是最直接的方法。比如 Q2 里的笛卡尔积导致算出的 GMV 虚高（把 SP 州的营收算成了 220 万），或者 Q3 里匹配成功率极低，我立刻就知道 AI 的 JOIN 逻辑或匹配维度出错了。
2. **对照业务常识**：AI 写的代码逻辑能跑通，但业务结果不合理。比如 Q1 里匿名用户买的 Top 1 商品竟然是“邮费”，这就逼迫我进一步去分析人群画像，而不是无脑相信 AI 的数据清洗建议。
3. **看执行性能**：只要 AI 敢用 `iterrows` 处理百万级数据，跑几秒钟我就知道代码不能要了。

### 一句话总结你的 AI 使用心得

AI 可以帮助编写冗长和复杂的代码，但是使用者必须去检查和设计架构以符合实际的业务要求，然后评估采用哪种方法。

---

**注：如果你的对话记录主要是截图，请在此目录创建 `ai_logs/` 子目录存放截图，并在本文档中引用：**

```markdown
![Q3.1 退货匹配讨论](./ai_logs/q3_returns_matching_1.png)
```
