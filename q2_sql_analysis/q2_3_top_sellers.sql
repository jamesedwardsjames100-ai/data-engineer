-- 1. 临时解除当前会话的超时限制（单位：毫秒，0 表示无限制）
SET SESSION max_execution_time = 0;

-- 2. 执行优化后的 SQL
WITH
-- 【1】评价去重
review_agg AS (
    SELECT order_id, AVG(review_score) AS order_avg_review
    FROM olist_order_reviews_dataset
    GROUP BY order_id
),
-- 【2】商品金额预聚合（不带大字段）
order_items_agg AS (
    SELECT seller_id, order_id, SUM(price + freight_value) AS order_gmv
    FROM olist_order_items_dataset
    GROUP BY seller_id, order_id
),
-- 【3】订单与客户基础信息（2024年时间过滤前置，提前收敛数据量）
order_customer_base AS (
    SELECT 
        o.order_id, 
        o.order_status, 
        o.order_delivered_customer_date, 
        o.order_estimated_delivery_date,
        c.customer_unique_id
    FROM olist_orders_dataset o
    JOIN olist_customers_dataset c ON o.customer_id = c.customer_id
    WHERE o.order_purchase_timestamp >= '2017-01-01'
      AND o.order_purchase_timestamp <  '2018-01-01'
),
-- 【4】卖家-订单核心关联（只包含聚合所需的最小必要字段）
seller_order_detail AS (
    SELECT
        oia.seller_id,
        oia.order_id,
        oia.order_gmv,
        ocb.order_status,
        ocb.order_delivered_customer_date,
        ocb.order_estimated_delivery_date,
        ocb.customer_unique_id,
        ra.order_avg_review
    FROM order_items_agg oia
    JOIN order_customer_base ocb ON oia.order_id = ocb.order_id
    LEFT JOIN review_agg ra ON ocb.order_id = ra.order_id
),
-- 【5】卖家维度聚合
seller_agg AS (
    SELECT
        sod.seller_id,
        SUM(sod.order_gmv)                                   AS gmv_2017,
        COUNT(DISTINCT sod.order_id)                         AS order_count,
        COUNT(DISTINCT sod.customer_unique_id)               AS unique_customers,
        ROUND(AVG(sod.order_avg_review), 2)                  AS avg_review_score,
        
        -- 延迟率
        ROUND(
            SUM(CASE WHEN sod.order_delivered_customer_date IS NOT NULL
                      AND sod.order_estimated_delivery_date IS NOT NULL
                      AND sod.order_delivered_customer_date > sod.order_estimated_delivery_date
                     THEN 1 ELSE 0 END) * 100.0
            / NULLIF(
                SUM(CASE WHEN sod.order_delivered_customer_date IS NOT NULL
                          AND sod.order_estimated_delivery_date IS NOT NULL
                         THEN 1 ELSE 0 END), 0), 
            2)                                               AS late_delivery_rate,
            
        -- 取消率
        ROUND(
            SUM(CASE WHEN sod.order_status = 'canceled' THEN 1 ELSE 0 END) * 100.0
            / NULLIF(COUNT(DISTINCT sod.order_id), 0), 
            2)                                               AS cancel_rate
    FROM seller_order_detail sod
    GROUP BY sod.seller_id
),
-- 【6】州内排名（使用全量卖家聚合结果计算 RANK）
seller_ranked AS (
    SELECT 
        sa.*, 
        s.seller_state,
        RANK() OVER (PARTITION BY s.seller_state ORDER BY sa.gmv_2017 DESC) AS state_rank
    FROM seller_agg sa
    JOIN olist_sellers_dataset s ON sa.seller_id = s.seller_id
)
-- 【7】截取全国 GMV TOP 20
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
