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
/*
==================================================
【进阶方案与利弊分析】
==================================================

方案 1：人工补录
- 操作：新建一个临时表，由懂葡萄牙语的业务人员或通过 Google 翻译，把缺失的词补全后，再 UNION 回翻译表中。
- 利：数据最准确，一劳永逸，符合数据治理规范。
- 弊：维护成本高，如果是每天新增的实时数据，人工来不及处理。

方案 2：源词兜底
- 操作：在 ETL 或前端展示时，使用 COALESCE(t.product_category_name_english, p.product_category_name) 处理，没有英文直接显示葡萄牙语原词。
- 利：实施成本极低，保证数据不丢失。
- 弊：对英文用户不友好，体验差。

方案 3：AI 自动翻译
- 操作：在数据管道中写一段 Python 脚本，利用大模型（如 GPT/DeepSeek）读取缺失类别，自动生成英文翻译并写回数据库。
- 利：全自动化，处理海量数据效率高。
- 弊：可能存在翻译不准确或幻觉，需要加入人工抽检机制，且会产生一定的 API 调用成本。
*/
