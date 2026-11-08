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