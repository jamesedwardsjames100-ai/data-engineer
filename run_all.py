# run_all.py
# -*- coding: utf-8 -*-
"""
全链路 Pipeline 调度主控脚本
负责按顺序调用数据下载、数据质量、SQL导入、ETL清洗、LLM抽取等模块。
具备子进程隔离、UTF-8 强制编码、耗时统计与单模块容错机制。
"""

import subprocess
import sys
import time
import os

# 强制 Windows 终端输出 UTF-8，防止中文/Emoji 乱码引发崩溃
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def run_module(script_path, module_name):
    """执行单个模块，包含异常捕获和耗时统计"""
    print(f"\n{'=' * 60}")
    print(f"▶️ 正在执行模块: [{module_name}] -> {script_path}")
    print(f"{'=' * 60}")
    
    start_time = time.time()
    
    # 强制子进程也使用 UTF-8 编码，杜绝 GBK 报错
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    try:
        # 运行子进程
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=False, # 设置为 False 让子脚本的日志直接打印到控制台
            text=True,
            encoding='utf-8',
            env=env,
            check=True            # 如果子进程返回非 0，抛出 CalledProcessError
        )
        
        elapsed = time.time() - start_time
        print(f"✅ [{module_name}] 执行成功！耗时: {elapsed:.2f} 秒")
        
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start_time
        print(f"❌ [{module_name}] 执行失败！耗时: {elapsed:.2f} 秒")
        print(f"⚠️ 调度器捕获到异常，将跳过该模块，继续执行后续任务...")
    except Exception as e:
        print(f"❌ [{module_name}] 发生系统未知错误: {e}")
        print(f"⚠️ 调度器将继续执行后续任务...")


def main():
    print(" [START] Gekko Lab 数据工程全链路 Pipeline 启动 ")
    total_start_time = time.time()
    
    # 按照业务依赖顺序定义任务列表 (模块名, 脚本路径)
    tasks = [
        ("模块 0: 数据下载", "download_data.py"),
        ("模块 1: 数据质量探查", "q1_data_quality/q1_code.py"),
        ("模块 2: 数据入库 MySQL", "q2_sql_analysis/load_olist.py"),
        ("模块 3: ETL 核心管道", "q3_etl_pipeline/pipeline.py"),
        ("模块 4: LLM 结构化抽取", "q4_llm_extraction/extract_reviews.py")
    ]
    
    for module_name, script_path in tasks:
        if not os.path.exists(script_path):
            print(f"\n❌ 找不到脚本文件: {script_path}，跳过该模块。")
            continue
            
        run_module(script_path, module_name)
        
    total_elapsed = time.time() - total_start_time
    print(f"\n{'=' * 60}")
    print(f"🎉🎉🎉 [FINISH] 所有调度任务结束！总耗时: {total_elapsed:.2f} 秒 🎉🎉🎉")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()