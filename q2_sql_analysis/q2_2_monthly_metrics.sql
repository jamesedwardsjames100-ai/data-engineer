-- ============================================================
-- 按月份统计平台真实成交情况（财务口径：钱货两清）
--
-- 结构：
--   item_agg    : order_items 按 order_id 预聚合 → 消除 1:N 膨胀
--   order_base  : orders LEFT JOIN item_agg (1:1)，并计算布尔列
--                 is_really_delivered = 状态已送达 且 送达日期非空
--   主查询      : 用 is_really_delivered 做条件聚合，简化 CASE
--
-- 口径说明：
--   - delivered_orders / delivered_gmv / avg_delivery_days 共用
--     同一"真实送达"定义，保证报表内部自洽
--   - cancel_rate 分母 = 当月总单量（BI 口径）
--   - delivered_no_date_gmv 用于对账：状态 delivered 但送达日期缺失
--     的订单金额，此前会在月度汇总中"消失"
-- ============================================================

WITH item_agg AS (
    -- 预聚合：每个订单的 GMV（price + freight_value 累加）
    SELECT
        order_id,
        SUM(price + freight_value)   AS order_gmv
    FROM olist_order_items_dataset
    GROUP BY order_id
),
order_base AS (
    -- orders 与 item_agg 1:1 关联，并提前计算"真实送达"布尔标记
    SELECT
        o.order_id,
        o.order_purchase_timestamp,
        o.order_status,
        o.order_delivered_customer_date,
        COALESCE(ia.order_gmv, 0)    AS order_gmv,
        CASE
            WHEN o.order_status = 'delivered'
             AND o.order_delivered_customer_date IS NOT NULL
            THEN 1
            ELSE 0
        END                          AS is_really_delivered
    FROM olist_orders_dataset AS o
    LEFT JOIN item_agg         AS ia
           ON o.order_id = ia.order_id
)
SELECT
    DATE_FORMAT(ob.order_purchase_timestamp, '%Y-%m')                AS month,
    COUNT(*)                                                         AS total_orders,

    SUM(ob.is_really_delivered)                                      AS delivered_orders,

    SUM(CASE WHEN ob.order_status = 'canceled' THEN 1 ELSE 0 END)    AS canceled_orders,

    -- 取消率：分母为当月总单量（BI 口径）
    ROUND(
        SUM(CASE WHEN ob.order_status = 'canceled' THEN 1 ELSE 0 END) * 100.0
        / NULLIF(COUNT(*), 0),
        2
    )                                                                AS cancel_rate,

    -- 已确认收入 GMV：只算钱货两清的单
    ROUND(
        SUM(CASE WHEN ob.is_really_delivered = 1 THEN ob.order_gmv ELSE 0 END),
        2
    )                                                                AS delivered_gmv,

    -- 对账盲区：状态 delivered 但送达日期缺失的金额
    ROUND(
        SUM(CASE WHEN ob.order_status = 'delivered'
                  AND ob.order_delivered_customer_date IS NULL
                 THEN ob.order_gmv ELSE 0 END),
        2
    )                                                                AS delivered_no_date_gmv,

    -- 平均送达天数：仅真实送达单参与，AVG 自动忽略 NULL
    ROUND(
        AVG(
            CASE WHEN ob.is_really_delivered = 1
                 THEN DATEDIFF(
                        ob.order_delivered_customer_date,
                        ob.order_purchase_timestamp
                      )
            END
        ),
        2
    )                                                                AS avg_delivery_days

FROM order_base AS ob
GROUP BY month
ORDER BY month;
