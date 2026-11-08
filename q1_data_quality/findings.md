### 问题 1：`InvoiceNo` 不只是数字

**支持代码**：

import pandas as pd

# 1. 读取数据
df = pd.read_csv("data/online_retail_ii.csv", encoding='ISO-8859-1')

# 2. 找出包含字母的发票号 (排除纯数字)
letter_invoices = df[df['Invoice'].astype(str).str.contains('[A-Za-z]', na=False)]

# 3. 提取前缀字母并统计出现次数
# r'^([A-Za-z]+)' 的意思是：提取字符串开头连续的字母
prefixes = letter_invoices['Invoice'].astype(str).str.extract(r'^([A-Za-z]+)')[0]
print("=== 非纯数字发票号的前缀统计 ===")
print(prefixes.value_counts())

# 4. 打印这些记录的特征，让你“眼见为实”
print("\n=== 带 'C' 前缀的发票示例 (观察数量/单价) ===")
print(letter_invoices[letter_invoices['Invoice'].str.startswith('C')][['Invoice', 'Quantity', 'Price', 'Description']].head(5))

print("\n=== 带 'A' 前缀的发票示例 (观察数量/单价) ===")
print(letter_invoices[letter_invoices['Invoice'].str.startswith('A')][['Invoice', 'Quantity', 'Price', 'Description']].head(5))

**简短解读**：
#探查结果：

C 前缀：出现 19,494 次。

A 前缀：出现 6 次。

#业务含义解读：

C (Cancellation)：代表取消订单/退货。观察特征发现，这些记录的Quantity全部为负数。

A (Adjustment)：代表财务调整/坏账。通常伴随极大的负数价格（如 -53594.36），描述为 Adjust bad debt。

在计算销售总额（GMV）时，必须剔除 C 和 A 开头的记录。如果用 Quantity * Price 直接求和，退货和坏账的负数值会直接抵消掉正常交易的正数值，导致公司真实营收被严重低估。

## 问题 2：`StockCode` 也不只是产品

**支持代码**：


import pandas as pd
import re

df = pd.read_csv("data/online_retail_ii.csv", encoding='ISO-8859-1')
df['TotalAmount'] = df['Quantity'] * df['Price']

# 逻辑：正常的商品代码要么全是数字，要么是"数字+一个字母"（如 85123A）。
# 我们筛选出不符合这个规律的非产品代码
valid_pattern = r'^\d+[A-Z]?$' 
non_product = df[~df['StockCode'].astype(str).str.match(valid_pattern)]

print("=== 非产品代码 TOP 10 ===")
print(non_product['StockCode'].value_counts().head(10))

# 计算行数和金额占比
row_ratio = len(non_product) / len(df) * 100
amount_ratio = non_product['TotalAmount'].sum() / df['TotalAmount'].sum() * 100

print(f"\n占总体行数比例: {row_ratio:.4f}%")
print(f"占总体金额比例: {amount_ratio:.4f}%")

**简短解读**：

探查结果与占比：

这部分记录占总行数比例为 1.0061%，占总金额比例为 0.0791%。

通过正则排查，抓出了两类异常代码：

业务特殊代码：如 POST（邮费，2122条）、DOT（运费，1446条）、M（手工调整，1421条）、C2（物流商）、D（折扣）。
录入不规范代码：如 15056BL（923条）、79323LP（232条）。这实际上是员工录入时多加了后缀字母（如颜色/尺码），它们本质上是实体商品。
业务解读：

针对 POST/DOT/M 等：代表附加服务或财务调整，不能计入商品销量，但在做全站营收核算时，它们是客户实际支付的金额，应作为“其他收入”单列。

针对 15056BL 等：通过观察其 Price 和 Description，发现是真实的商品交易。在数据清洗时，可以通过截取前 5 位或前 6 位字符串的方式，将它们清洗回正常的 StockCode，而不是简单删除。

## 问题 3：可疑的极端值

**支持代码**：

import pandas as pd

# 1. 读取数据
df = pd.read_csv("data/online_retail_ii.csv", encoding='ISO-8859-1')

# 2. 找出 Quantity 为 80995 或 -80995 的极值记录
print("=== 1. Quantity 极值记录 (80995 / -80995) ===")
extreme_qty = df[df['Quantity'].isin([80995, -80995])]
print(extreme_qty[['Invoice', 'StockCode', 'Quantity', 'Price', 'Description']])
# 顺便把这几条记录的 TotalAmount 算出来看看
extreme_qty_total = extreme_qty['Quantity'] * extreme_qty['Price']
print(f"极值记录产生的金额: {extreme_qty_total.sum()}")

# 3. 找出 Price (即题目的 UnitPrice) 为负数的记录
print("\n=== 2. Price 为负值的记录 ===")
negative_price = df[df['Price'] < 0]
print(negative_price[['Invoice', 'StockCode', 'Quantity', 'Price', 'Description']])

**简短解读**：

任务一：Quantity 极值是真实业务还是数据错误？

一条是 Invoice=581483，Quantity=80995；紧接着下一条是 Invoice=C581484，Quantity=-80995。两者的 StockCode 均为 23843，单价均为 2.08，描述均为 PAPER CRAFT , LITTLE BIRDIE。这是系统录入错误导致的数据错误。极大概率是操作员在输入数量时多按了几个数字（把 80 当成了 80995），随后系统或人工发现异常，立刻生成了一张 C 开头的取消单进行冲销（所以一正一负金额刚好为 0）。

任务二：UnitPrice 为负的记录有什么共同特征？业务上代表什么？

价格全部为 5 位数的极大负值（如 -53594.36）；Invoice 全部以 A 开头；StockCode 固定为 B；Description 均为 Adjust bad debt。这是财务部门进行的坏账核销（调账）操作。当客户的欠款被确认为无法收回的坏账时，财务系统会通过负金额扣除相应的应收账款，以此来平账。

任务三：作为数据工程师，保留还是删除？说明判断标准

绝对不能一刀切盲目删除，要根据下游用途决定。针对 BI / 销售报表：必须过滤剔除。极值冲销记录会干扰正常的销售统计；坏账调整也会严重拉低真实的商品 GMV。
针对风控 / 异常检测模型：必须保留。录入错误（如多打几个 9）和坏账核销，恰恰是识别系统漏洞、员工操作失误、甚至是金融欺诈的最有价值的“异常样本”，删除会导致模型丧失识别风险的能力。

## 问题 4：CustomerID 的“沉默大多数”

**支持代码**：

import pandas as pd

# 1. 读取数据并计算总金额
df = pd.read_csv("data/online_retail_ii.csv", encoding='ISO-8859-1')
df['TotalAmount'] = df['Quantity'] * df['Price']

# 2. 拆分数据集：匿名用户 vs 实名用户
missing_cid = df[df['Customer ID'].isnull()]
valid_cid = df[df['Customer ID'].notnull()]

# 3. 计算行数占比与金额占比
row_ratio = len(missing_cid) / len(df) * 100
amount_ratio = missing_cid['TotalAmount'].sum() / df['TotalAmount'].sum() * 100

print(f"=== 占比分析 ===")
print(f"匿名记录占总行数比例: {row_ratio:.2f}%")
print(f"匿名记录占总金额比例: {amount_ratio:.2f}%")

# 4. 对比国家分布 (TOP 3)
print("\n=== 国家分布对比 ===")
print("匿名用户 TOP 3 国家:")
print(missing_cid['Country'].value_counts().head(3))
print("\n实名用户 TOP 3 国家:")
print(valid_cid['Country'].value_counts().head(3))

# 5. 对比客单价 (平均每笔订单金额)
print("\n=== 客单价对比 ===")
print(f"匿名用户平均客单价: {missing_cid['TotalAmount'].mean():.2f}")
print(f"实名用户平均客单价: {valid_cid['TotalAmount'].mean():.2f}")

# 6. 对比高频商品 (TOP 5)
print("\n=== 高频商品对比 ===")
print("匿名用户购买 TOP 5 商品:")
print(missing_cid['Description'].value_counts().head(5))
print("\n实名用户购买 TOP 5 商品:")
print(valid_cid['Description'].value_counts().head(5))

**简短解读**：

任务一：算出确切比例

缺失 Customer ID 的记录有 22.77%（共 243,007 条），这部分缺失记录占总金额的 13.68%。人数虽然挺多（占了近四分之一），但贡献的营收却不到七分之一，这说明这批用户的购买力显著低于实名用户。

任务二：维度差异对比

匿名用户极度集中在英国本土（240,029 条），而实名用户除了英国，还有大量来自德国（17,624 条）、爱尔兰等地的国际订单，这说明匿名用户多为本土行为。匿名用户平均客单价为 10.86，而实名用户为 20.20，是前者的近两倍。

匿名用户的 TOP 1 是 DOTCOM POSTAGE（邮费），且购买了大量的 JUMBO BAG（大号包装袋）。
实名用户购买的多为高附加值商品，如 WHITE HANGING HEART T-LIGHT HOLDER（心形烛台）、REGENCY CAKESTAND（蛋糕架）等。

任务三：人群推测
综合以上数据，推测这批“匿名群体”大概率是以下几类人群：

线下实体店散客，因为他们买包装袋（JUMBO BAG）且无需注册账号。

未登录的“补邮费”客户，TOP 1 的邮费商品说明大量匿名订单是为了单独支付运费或补差价。

一次性游客或低净值客户，因为客单价极低，买完就走，没有复购意愿，因此不愿走繁琐的注册流程。
