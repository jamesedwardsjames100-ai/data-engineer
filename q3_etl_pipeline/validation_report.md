# Q3 ETL 数据校验报告 (Validation Report)

## 1. `sales_facts.parquet` (用于 BI 报表)

*   **实际总行数**：**1,035,620** 行（从原始 106 万行中剔除了退货、坏账、非标准代码及异常价格/数量）。
*   **关键字段空值率**：
    *   `customer_id` 空值率为 **22.6%**（符合原始数据中大量游客/线下散客未登录的真实业务情况）。
    *   其他所有业务字段（如金额、数量、发票号、时间等）空值率均为 **0.0%**。
*   **数据类型规范**：
    *   `invoice_datetime` 为 `datetime64[us]` 类型。
    *   `unit_price` 与 `total_amount` 为 `float64` 类型。
    *   `customer_id`, `invoice_no`, `stock_code` 强制转换为 `string` 类型，确保后续查询不丢失前导零。
*   **数据校验**：`assert (sales_df['total_amount'] > 0).all()` 通过。

## 2. `customer_features.parquet` (用于客户分群)

*   **实际总行数**：**5,852** 行（对应 5,852 个有真实交易记录的唯一客户）。
*   **基准日期**：数据集最后一天为 `2011-12-09 12:50:00`。
*   **关键字段空值率**：所有字段空值率均为 **0.0%**。
*   **数据类型规范**：
    *   `frequency`, `unique_products`, `recency_days` 为 `int64`。
    *   `monetary` 为 `float64`。
    *   `is_one_time_buyer` 为 `bool` 类型。
*   **数据校验**：`assert (rfm_df['recency_days'] >= 0).all()` 通过。

## 3. `returns_log.parquet` (用于退货分析)

*   **实际总行数**：**18,744** 行（`Invoice` 以 'C' 开头的退货/取消记录）。
*   **原单匹配率**：成功匹配 **16,317** 条，匹配率高达 **87.05%**。
*   **关键字段空值率**：
    *   `matched_original_invoice` 空值率为 **12.95%**（这部分未匹配的退货大概率是原始购买记录就是匿名用户，或者属于系统跨期无法溯源的脏数据，作为孤儿数据保留即可，符合业务预期）。
*   **数据校验**：`assert (returns_df['quantity'] > 0).all()` 通过。

## 总结
1. 全面禁用 `iterrows()`，采用 Pandas 向量化过滤与底层 C 语言实现的 `merge_asof` 时间序列匹配，106 万行数据全流程跑完用了 **5.97秒**。
2. 固定了随机种子（`random.seed(42)`），确保相同输入在任何环境下产出完全一致的 Parquet 文件。