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
    