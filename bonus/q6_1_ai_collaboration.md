# Q6.1 - AI 协作反向分析（选做，10 分）

请选择本试卷中你认为**最有挑战的一道题**，做以下分析：

## 选定的题目：退货匹配（Q3.1 最难的部分）_

## 1. 你的第一个 Prompt

```
你是一个资深的数据工程师。我要处理 100 万行零售数据的退货匹配。帮我写个 Python 脚本，把订单表里 Invoice 以 'C' 开头的退货记录找出来，并在原始销售表里找到它对应的原订单号。如果有多笔满足条件，就找离退货时间最近的那一笔。
```

**为什么这样写**：

一开始，我只关注了业务逻辑的直观表达，想用最直白的语言让 AI 把业务常识翻译成代码。我当时完全没意识到百万级数据量下的性能陷阱，也没考虑到复杂的业务边界情况。

---

## 2. AI 的回答

```
你可以使用 Pandas 遍历数据。以下是代码示例：
for idx, row in returns_df.iterrows():
    valid_sales = sales_df[(sales_df['Customer ID'] == row['Customer ID']) & 
                           (sales_df['StockCode'] == row['StockCode']) & 
                           (sales_df['InvoiceDate'] < row['InvoiceDate'])]
    if not valid_sales.empty:
        matched_invoice = valid_sales.sort_values('InvoiceDate').iloc[-1]['Invoice']
```

---

## 3. 你迭代了几轮 Prompt？

3轮
---

## 4. AI 的最终答案有什么错误或不足？

> 你是怎么发现并修正的？


AI 的错误1：AI 直接抛出了 Pandas 的 iterrows 嵌套循环。在 100 万行数据量下，这种 
O(N×M) 的复杂度绝对会导致 OOM 或跑上几个小时。

我的修正：我指出性能问题，强制要求 AI 改用基于底层二分查找的 pandas.merge_asof 进行时间序列匹配。


AI 的错误2：AI 给出的 merge_asof 改进版中，在 by 参数里强行加入了 quantity（数量）。但真实的电商场景是：“客户买 10 个商品，分两次退货（每次退 5 个）”。如果严格匹配数量，这两笔退货将永远找不到原单。

我的修正：我人工干预，删除了 by 中的 quantity 限制。只要 customer_id 和 stock_code 一致，就向前找最近的购买记录。这让匹配率大幅提升，最终达到 87%。


AI 的错误3：代码逻辑完全正确，但实际一跑就报 MergeError。因为经过清洗的 customer_id 变成了 Pandas 的 string 类型（包含 <NA> 空值），而原表里的 nan 是不同的底层类型，两者在 merge_asof 时直接崩溃。

我的修正：手动在合并前加了强制降级：returns_df['customer_id'] = returns_df['customer_id'].astype(str)，将扩展类型转为最原始的对象，解决崩溃。

---

## 5. 如果让你再做一次同样的题，你的第一个 prompt 会怎么写？

你是一个资深的数据工程师。请使用 Pandas 完成退货单的原单回溯匹配。
要求：
1. 数据量级 100 万行，严禁使用 iterrows 或 apply 循环。
2. 必须使用 merge_asof 进行时间序列的二分查找匹配。
3. 两表合并前，必须先按 invoice_datetime 升序排序。
4. 匹配维度：只按 customer_id 和 stock_code 匹配。严禁加入 quantity 字段，以解决真实世界中“买10个分2次退5个”的批量退货场景。
5. 匹配方向：设置 direction='backward'（找退货时间之前最近的一笔）。
6. 防御 Pandas 报错：合并前必须确保关联键被强制转换为原生字符串类型（如 df['id'].astype(str)），防止 StringDtype 与 NaN 在 merge_asof 时发生冲突。

---

## 评分排序

- 8-10 分：能精准识别 AI 答案的盲区，并给出值得记录的"Prompt 工程"经验
- 5-7 分：使用 AI 但能识别基础错误
- 1-4 分：完全依赖 AI，无独立判断
- **0 分**：没用 AI 但题目做对了（不扣分，加分题不得分）
