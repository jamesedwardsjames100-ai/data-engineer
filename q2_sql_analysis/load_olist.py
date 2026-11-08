# load_olist.py
"""
把 data/olist/ 目录下的 9 个 CSV 导入本地 MySQL 8.0 的 olist 数据库。

路径定位策略（向上查找，兼容脚本放在子目录）:
    - 从脚本所在目录开始，逐级向上找 data/olist/，找到即用
    - 若设置了环境变量 OLIST_DIR 则优先使用（方便 CI / 特殊布局覆盖）

其余约束:
  - 数据库 olist（不存在则创建, utf8mb4），账号 root / 密码 123456
  - 表名 = CSV 文件名去 .csv 后缀
  - 每文件独立 try-except，成功打印行数
"""

import os
import sys

import pandas as pd
from sqlalchemy import create_engine, text

# ---------------- 配置 ----------------
DB_USER = "root"
DB_PASS = "521366"
DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_NAME = "olist"
CHARSET = "utf8mb4"

SERVER_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/?charset={CHARSET}"
)
DB_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset={CHARSET}"
)


def find_olist_dir(max_up: int = 5) -> str | None:
    """从脚本目录向上查找 data/olist/，返回绝对路径或 None。

    支持环境变量 OLIST_DIR 覆盖（用于非标准目录布局）。
    """
    env_dir = os.environ.get("OLIST_DIR")
    if env_dir and os.path.isdir(env_dir):
        return os.path.abspath(env_dir)

    cur = os.path.dirname(os.path.abspath(__file__))
    tried = []
    for _ in range(max_up + 1):
        candidate = os.path.join(cur, "data", "olist")
        tried.append(candidate)
        if os.path.isdir(candidate):
            return candidate
        parent = os.path.dirname(cur)
        if parent == cur:      # 已到盘符根
            break
        cur = parent

    print("[错误] 未能定位 data/olist/ 目录，已尝试：", file=sys.stderr)
    for p in tried:
        print(f"  - {p}", file=sys.stderr)
    return None


def ensure_database() -> None:
    engine = create_engine(SERVER_URL, echo=False)
    try:
        with engine.begin() as conn:
            conn.execute(text(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                f"DEFAULT CHARACTER SET {CHARSET} "
                f"COLLATE {CHARSET}_unicode_ci"
            ))
        print(f"[DB] 确认数据库 `{DB_NAME}` 就绪")
    finally:
        engine.dispose()


def load_one(engine, csv_path: str, table_name: str) -> int:
    df = pd.read_csv(csv_path)
    df.to_sql(
        table_name,
        engine,
        if_exists="replace",
        index=False,
        chunksize=10000,
        method="multi",
    )
    return len(df)


def main() -> None:
    olist_dir = find_olist_dir()
    if olist_dir is None:
        print("提示：可手动把 Olist CSV 放到项目根目录的 data/olist/，"
              "或设置环境变量 OLIST_DIR 指向已有目录。", file=sys.stderr)
        sys.exit(1)

    csv_files = sorted(
        f for f in os.listdir(olist_dir) if f.lower().endswith(".csv")
    )
    if not csv_files:
        print(f"[错误] {olist_dir} 下没有 CSV 文件", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] 数据目录: {olist_dir}")
    print(f"[INFO] 待导入 {len(csv_files)} 个 CSV\n")

    ensure_database()
    engine = create_engine(DB_URL, echo=False)

    results = []
    for fname in csv_files:
        table_name = os.path.splitext(fname)[0]
        csv_path = os.path.join(olist_dir, fname)
        try:
            rows = load_one(engine, csv_path, table_name)
            print(f"[OK]   {table_name:<40s} rows = {rows:,}")
            results.append((table_name, rows, "OK"))
        except Exception as exc:
            print(f"[FAIL] {table_name:<40s} {type(exc).__name__}: {exc}")
            results.append((table_name, 0, f"FAIL: {type(exc).__name__}"))

    engine.dispose()

    ok = sum(1 for _, _, s in results if s == "OK")
    print(f"\n{'=' * 60}")
    print(f"完成: {ok}/{len(results)} 张表导入成功")
    if ok != len(results):
        print("失败明细:")
        for name, _, status in results:
            if status != "OK":
                print(f"  - {name}: {status}")
        sys.exit(2)


if __name__ == "__main__":
    main()