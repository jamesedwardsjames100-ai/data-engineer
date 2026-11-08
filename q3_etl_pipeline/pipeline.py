# pipeline.py
# -*- coding: utf-8 -*-
"""
电商数据 ETL Pipeline：清洗 100 万行 Online Retail II 数据
包含：环境初始化、日志配置、模块化拆分、强断言校验、向量化计算、Parquet 落地、内存峰值追踪。
"""

import os
import time
import random
import logging
import pandas as pd
import numpy as np
import tracemalloc  # 👈 新增：用于追踪内存峰值

# ==========================================
# 🚨 全局环境与随机种子配置
# ==========================================
random.seed(42)
np.random.seed(42)

# 动态获取脚本所在目录及上级项目根目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)

# 1. 创建输出与日志目录（全部使用绝对路径，防止相对路径乱跑）
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "outputs")
LOG_DIR = SCRIPT_DIR
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
        df = df.rename(columns={'UnitPrice': 'Price'})

    # 1. InvoiceDate 转 datetime
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])

    # 2. Customer ID 处理：使用正则去除 .0，并将 nan 替换为 None
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
    mask_stock = df['StockCode'].astype(str).str.match(r'^\d+[A-Za-z]?$', na=False)

    # 3. 剔除 Quantity <= 0 或 Price <= 0 的异常值
    mask_valid = (df['Quantity'] > 0) & (df['Price'] > 0)

    # 过滤并深拷贝
    sales_df = df[mask_invoice & mask_stock & mask_valid].copy()

    # 计算 total_amount
    sales_df['total_amount'] = sales_df['Quantity'] * sales_df['Price']

    # 4. 重命名与类型强转 (移除 inplace)
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
    sales_df = sales_df.rename(columns=rename_map)

    # 仅保留 9 个要求字段
    cols = ['invoice_no', 'stock_code', 'description', 'quantity', 
            'unit_price', 'total_amount', 'invoice_datetime', 'customer_id', 'country']
    sales_df = sales_df[cols]

    # 强制转换数据类型
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
    def safe_mode(x):
        m = x.mode()
        return m.iloc[0] if not m.empty else None

    rfm_df = valid_df.groupby('customer_id').agg(
        last_purchase_date=('invoice_datetime', 'max'),
        first_purchase_date=('invoice_datetime', 'min'),
        frequency=('invoice_no', 'nunique'),         
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
    
    returns_df = returns_df[['Invoice', 'StockCode', 'Quantity', 'InvoiceDate', 'Customer ID']]
    
    # 移除 inplace
    returns_df = returns_df.rename(columns={
        'Invoice': 'return_invoice_no',
        'StockCode': 'stock_code',
        'Quantity': 'quantity',
        'InvoiceDate': 'invoice_datetime',
        'Customer ID': 'customer_id'
    })
    
    returns_df = returns_df.dropna(subset=['customer_id'])

    # 2. 准备正向销售记录
    sales_pos = sales_df[['invoice_no', 'customer_id', 'stock_code', 'invoice_datetime']].copy()
    sales_pos = sales_pos.rename(columns={'invoice_no': 'matched_original_invoice'})

    # 🚨 核心修复：强制统一 merge_asof 的 by 键类型 (转为普通 str)
    # 避免 StringDtype(na_value=nan) 和 StringDtype(na_value=<NA>) 冲突
    returns_df['customer_id'] = returns_df['customer_id'].astype(str)
    returns_df['stock_code'] = returns_df['stock_code'].astype(str)
    sales_pos['customer_id'] = sales_pos['customer_id'].astype(str)
    sales_pos['stock_code'] = sales_pos['stock_code'].astype(str)

    # 3. merge_asof 强制要求：两表必须按时间字段全局排序
    returns_df = returns_df.sort_values('invoice_datetime')
    sales_pos = sales_pos.sort_values('invoice_datetime')

    # 4. 执行 merge_asof
    matched_returns = pd.merge_asof(
        returns_df,
        sales_pos,
        on='invoice_datetime',
        by=['customer_id', 'stock_code'],
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

    assert (sales_df['total_amount'] > 0).all(), "异常：sales_df 存在总金额 <= 0 的数据"
    assert (rfm_df['recency_days'] >= 0).all(), "异常：rfm_df 存在负数间隔天数"
    assert (returns_df['quantity'] > 0).all(), "异常：returns_df 存在 <= 0 的退货数量"

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
    
    # 👈 新增：开始追踪内存分配
    tracemalloc.start()
    
    # 智能探测数据文件路径
    file_paths = [
        os.path.join(BASE_DIR, "data", "online_retail_ii.csv"),
        os.path.join(BASE_DIR, "data", "online-retail-ii.csv")
    ]
    
    input_file = None
    for p in file_paths:
        if os.path.exists(p):
            input_file = p
            break
            
    if not input_file:
        logger.error(f"找不到数据文件！请确认以下路径之一存在：\n{file_paths[0]}\n{file_paths[1]}")
        return
        
    try:
        # 1. 数据加载
        raw_df = load_data(input_file)
        
        # 2. 真实销售处理
        sales_df = filter_real_sales(raw_df)
        
        # 3. 客户分群
        rfm_df = compute_rfm(sales_df)
        
        # 4. 退货分析
        returns_df = match_returns(raw_df, sales_df)
        
        # 5. 终局校验
        validate_output(sales_df, rfm_df, returns_df)
        
        # 6. 文件落地
        logger.info(f"开始写入 Parquet 文件至 {OUTPUT_DIR}...")
        sales_df.to_parquet(os.path.join(OUTPUT_DIR, "sales_facts.parquet"), index=False)
        rfm_df.to_parquet(os.path.join(OUTPUT_DIR, "customer_features.parquet"), index=False)
        returns_df.to_parquet(os.path.join(OUTPUT_DIR, "returns_log.parquet"), index=False)
        
        elapsed_time = time.time() - start_time
        
        # 👈 新增：获取内存峰值并转换为 MB
        current, peak = tracemalloc.get_traced_memory()
        peak_mb = peak / 1024 / 1024
        
        logger.info(f"🎉 Pipeline 运行圆满成功！总耗时: {elapsed_time:.2f} 秒。")
        logger.info(f"📊 内存峰值: {peak_mb:.2f} MB")
        
    except Exception as e:
        logger.error(f"❌ Pipeline 执行中断，发生异常: {e}", exc_info=True)
    finally:
        # 👈 新增：确保在任何情况下都停止追踪
        tracemalloc.stop()

if __name__ == "__main__":
    main()