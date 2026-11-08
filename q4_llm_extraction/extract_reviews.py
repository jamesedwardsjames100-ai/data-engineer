# extract_reviews.py
# -*- coding: utf-8 -*-
"""
电商差评结构化提取脚本 (全量生产版)
包含：规则分流、原生 HTTP、指数退避、断点续传、20线程狂暴并发、优雅退出。
"""

import os
import re
import json
import time
import requests
import pandas as pd
import concurrent.futures
from tqdm import tqdm
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

# ==========================================
# 🚨 全局配置
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)

REVIEWS_CSV = os.path.join(BASE_DIR, "data", "olist", "olist_order_reviews_dataset.csv")
PROMPT_FILE = os.path.join(SCRIPT_DIR, "prompt_template.txt")
OUTPUT_JSON = os.path.join(SCRIPT_DIR, "extracted_issues.json")
FAILED_TXT = os.path.join(SCRIPT_DIR, "failed_reviews.txt")

env_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path=env_path, override=True)
API_KEY = os.getenv("OPENAI_API_KEY")
API_URL = "https://api.deepseek.com/chat/completions" 

# 🚨 提速核心：直接把并发数拉满到 20
MAX_WORKERS = 20

if not API_KEY:
    raise ValueError("❌ 未找到 OPENAI_API_KEY，请检查 .env 文件！")

# ==========================================
# 核心功能
# ==========================================
def is_garbage_text(text: str) -> bool:
    if not isinstance(text, str):
        return True
    text = text.strip().lower()
    if len(text) < 5:
        return True
    garbage_words = {"ruim", "pessimo", "péssimo", "nao", "não", "muito ruim", "mto ruim", "recomendo", "bom", "otimo"}
    return text in garbage_words

def clean_markdown_json(raw_content: str) -> dict:
    content = re.sub(r'^```(?:json)?\s*', '', raw_content, flags=re.IGNORECASE)
    content = re.sub(r'\s*```$', '', content)
    try:
        return json.loads(content.strip())
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 解析失败，原始返回: {raw_content}") from e

@retry(
    stop=stop_after_attempt(3), 
    wait=wait_exponential(multiplier=1, min=2, max=10), 
    reraise=True
)
def call_deepseek_api(review_id: str, review_text: str, prompt_template: str) -> tuple:
    safe_text = str(review_text).replace('"', "'").replace('\n', ' ').replace('\r', ' ').strip()
    user_prompt = prompt_template.replace("{review_id}", str(review_id)).replace("{review_text}", safe_text)

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": user_prompt}],
        "temperature": 0.0
    }

    response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status() 
    
    resp_json = response.json()
    total_tokens = resp_json.get("usage", {}).get("total_tokens", 0)
    content = resp_json["choices"][0]["message"]["content"]
    
    parsed_data = clean_markdown_json(content)
    return parsed_data, total_tokens

def process_single_review(row, prompt_template):
    try:
        rid = str(row['review_id'])
        text = row['review_comment_message']
        parsed_json, tokens = call_deepseek_api(rid, text, prompt_template)
        return {"success": True, "data": parsed_json, "tokens": tokens, "review_id": rid}
    except Exception as e:
        return {"success": False, "error": str(e), "tokens": 0, "review_id": str(row['review_id'])}


def main():
    start_time = time.time()
    
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    print("正在加载并过滤评论数据...")
    df = pd.read_csv(REVIEWS_CSV)
    df_valid = df[(df['review_score'] <= 3) & df['review_comment_message'].notna()].copy()
    df_valid = df_valid[~df_valid['review_comment_message'].apply(is_garbage_text)]
    
    # 🔄 断点续传逻辑
    results = []
    processed_ids = set()
    
    if os.path.exists(OUTPUT_JSON):
        try:
            with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
                results = json.load(f)
                processed_ids = {str(item.get('review_id')) for item in results if 'review_id' in item}
            print(f"检测到历史进度：已成功提取 {len(results)} 条数据。")
        except Exception as e:
            print(f"读取历史结果失败，将重新开始: {e}")

    df_todo = df_valid[~df_valid['review_id'].astype(str).isin(processed_ids)]
    total_todo = len(df_todo)
    
    if total_todo == 0:
        print("🎉 所有数据都已处理完毕，无需运行！")
        return

    print(f"待处理数据: {total_todo} 条 | 并发线程数: {MAX_WORKERS}\n")
    
    total_tokens_used = 0
    success_count = 0
    
    # 🚀 多线程并发执行 (不使用 with 语句，改为手动管理，以便优雅处理 Ctrl+C)
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)
    futures = [executor.submit(process_single_review, row, prompt_template) for _, row in df_todo.iterrows()]
    
    try:
        for i, future in enumerate(tqdm(concurrent.futures.as_completed(futures), total=total_todo, desc="提取进度", unit="条")):
            res = future.result()
            
            if res["success"]:
                results.append(res["data"])
                total_tokens_used += res["tokens"]
                success_count += 1
            else:
                with open(FAILED_TXT, "a", encoding="utf-8") as f_fail:
                    f_fail.write(f"{res['review_id']}\n")
            
            # 💾 实时落盘
            if (i + 1) % 50 == 0 or (i + 1) == total_todo:
                with open(OUTPUT_JSON, "w", encoding="utf-8") as f_out:
                    json.dump(results, f_out, ensure_ascii=False, indent=2)
                    
    except KeyboardInterrupt:
        # 拦截 Ctrl+C，优雅退出
        print("\n⚠️ 检测到人工中断 (Ctrl+C)，正在保存当前进度并强制退出...")
        executor.shutdown(wait=False, cancel_futures=True)
        
        # 退出前最后保存一次
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f_out:
            json.dump(results, f_out, ensure_ascii=False, indent=2)
        print(f"✅ 数据已安全保存。下次运行将自动跳过 {len(results)} 条历史记录。")
        return

    executor.shutdown(wait=True)
    
    elapsed_time = time.time() - start_time
    print("\n" + "="*40)
    print(f"🎉 全量任务完成！成功提取 {success_count} 条，失败 {total_todo - success_count} 条。")
    print(f"📁 数据库累计总条数: {len(results)}")
    print(f"⏱️ 本轮总耗时: {elapsed_time:.2f} 秒 (约 {elapsed_time/60:.1f} 分钟)")
    print(f"🪙 本轮消耗 Token: {total_tokens_used}")
    print(f"💾 结果已保存至: {OUTPUT_JSON}")
    print("="*40)

if __name__ == "__main__":
    main()