# 客户财务管理功能优化说明

## 功能概述

本次优化完善了客户的期初欠款和储值管理功能,使其能够:
1. 在客户管理界面录入和修改期初欠款及储值
2. 自动记录期初欠款和储值的时间戳
3. 在对账单中显示期初欠款和储值记录
4. 按时间排序对账单(时间近的在前,远的在后)

## 数据库结构

### customers 表
```sql
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_code TEXT NOT NULL UNIQUE,
    customer_name TEXT NOT NULL,
    store_id INTEGER,
    contact_person TEXT,
    phone TEXT,
    address TEXT,
    balance REAL DEFAULT 0,              -- 储值余额
    balance_at TEXT,                      -- 储值调整时间
    initial_receivable REAL DEFAULT 0,    -- 期初欠款
    initial_receivable_at TEXT,           -- 期初欠款录入时间
    receivable REAL DEFAULT 0,            -- 当前应收欠款
    bank_name TEXT,
    bank_account TEXT,
    bank_code TEXT,
    tax_number TEXT,
    remark TEXT,
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT
)
```

## 业务逻辑

### 1. 新增客户
- 填入期初欠款(如50元),系统会:
  - 将 `initial_receivable` 设置为 50
  - 将 `initial_receivable_at` 设置为当前时间
  - 将 `receivable` 设置为 50 (期初欠款即为当前应收)

- 填入储值(如100元),系统会:
  - 将 `balance` 设置为 100
  - 将 `balance_at` 设置为当前时间

### 2. 修改客户
- **修改期初欠款**:
  - 输入新值(如80元): 更新 `initial_receivable` 为 80,更新 `initial_receivable_at` 为当前时间
  - 输入0或留空: 将 `initial_receivable` 设置为 0,清空 `initial_receivable_at`
  - 自动重新计算 `receivable` = (旧receivable - 旧initial_receivable + 新initial_receivable)

- **修改储值**:
  - 输入新值(如150元): 更新 `balance` 为 150,更新 `balance_at` 为当前时间
  - 输入0或留空: 将 `balance` 设置为 0,清空 `balance_at`

### 3. 对账单显示
在对账单接口 `/api/customers/:id/debt-details` 中:

- **期初欠款记录** (businessType: 'INITIAL'):
  ```json
  {
    "id": "initial-{customerId}",
    "businessDate": "{initial_receivable_at}",
    "docNumber": "期初欠款",
    "businessType": "INITIAL",
    "orderAmount": 50.00,
    "debtAmount": 50.00,
    "currentDebt": 50.00,
    "remark": "客户期初欠款"
  }
  ```

- **储值调整记录** (businessType: 'BALANCE'):
  ```json
  {
    "id": "balance-{customerId}",
    "businessDate": "{balance_at}",
    "docNumber": "储值调整",
    "businessType": "BALANCE",
    "balanceAmount": 100.00,
    "debtAmount": 0.00,
    "currentDebt": 50.00,
    "remark": "客户储值余额"
  }
  ```

### 4. 时间排序规则
对账单记录按以下顺序排序:
1. 首先按 `businessDate` (业务日期) 排序
2. 默认降序 (desc): 时间近的排在前面
3. 可点击排序按钮切换为升序 (asc): 时间远的排在前面
4. 相同日期按 `transactionId` 排序
5. 相同 `transactionId` 按 `id` 排序

## 前端界面

### 客户列表 (CustomerList.vue)
- 表格显示储值余额和应收欠款
- 点击编辑按钮打开编辑弹窗
- 编辑弹窗中有两个财务输入框:
  - **储值余额**: 支持输入数字,自动提示"修改后会更新储值调整时间"
  - **期初欠款**: 支持输入数字,自动提示"修改后会更新期初欠款时间,输入0或留空则删除"

### 对账单 (DebtDetails.vue)
- 顶部汇总卡片显示:
  - 应收欠款 = 期初欠款 + 增加应收欠款 - 收回欠款 - 优惠
  - 当前储值
- 筛选工具栏支持筛选业务类型:
  - 全部类型
  - 销售订单 (ORDER)
  - 退货单 (RETURN)
  - 收款单 (PAYMENT)
  - **期初欠款 (INITIAL)** - 黄色标签
  - **储值调整 (BALANCE)** - 蓝色标签
- 时间排序按钮,可切换升序/降序

## 使用示例

### 示例1: 新增客户并设置期初欠款
1. 点击"新增客户"按钮
2. 填写客户基本信息
3. 在"财务信息"部分:
   - 期初欠款: 输入 `50.00`
   - 储值余额: 输入 `100.00`
4. 点击"创建"
5. 系统自动记录:
   - `initial_receivable` = 50
   - `initial_receivable_at` = 当前时间
   - `balance` = 100
   - `balance_at` = 当前时间
   - `receivable` = 50

### 示例2: 修改客户的期初欠款
1. 在客户列表中点击"编辑"按钮
2. 修改期初欠款为 `80.00`
3. 点击"保存"
4. 系统自动:
   - 更新 `initial_receivable` = 80
   - 更新 `initial_receivable_at` = 当前时间
   - 重新计算 `receivable` = (旧receivable - 50 + 80)

### 示例3: 查看对账单
1. 在客户列表中点击客户编号或"查看详情"
2. 点击"查看对账单"或财务应收列表进入对账单页面
3. 对账单会显示:
   - 期初欠款记录(如果有)
   - 储值调整记录(如果有)
   - 所有订单、收款、退货记录
4. 默认按时间降序排列(最新的在上面)
5. 可点击排序按钮切换顺序

## API接口

### GET /api/customers
获取客户列表,返回包含 `balance` 和 `initialReceivable` 字段

### POST /api/customers
创建客户,请求体:
```json
{
  "customerName": "测试客户",
  "customerCode": "C001",
  "storeId": 1,
  "balance": 100.00,
  "initialDebt": 50.00
}
```

### PUT /api/customers/:id
更新客户,请求体同上

### GET /api/customers/:id/debt-details
获取客户对账单,返回:
```json
{
  "customerId": 1,
  "customerName": "测试客户",
  "initialDebt": 50.00,
  "storedBalance": 100.00,
  "totalReceivable": 50.00,
  "summary": {
    "initialDebt": 50.00,
    "storedBalance": 100.00,
    "receivableIncrease": 0.00,
    "debtRecovered": 0.00,
    "receivable": 50.00
  },
  "records": [
    {
      "id": "initial-1",
      "businessDate": "2026-03-11T10:30:00",
      "docNumber": "期初欠款",
      "businessType": "INITIAL",
      "orderAmount": 50.00,
      "debtAmount": 50.00,
      "currentDebt": 50.00
    },
    {
      "id": "balance-1",
      "businessDate": "2026-03-11T10:30:00",
      "docNumber": "储值调整",
      "businessType": "BALANCE",
      "balanceAmount": 100.00,
      "debtAmount": 0.00,
      "currentDebt": 50.00
    }
  ]
}
```

## 注意事项

1. **期初欠款与应收欠款的关系**:
   - 期初欠款是客户的历史欠款,作为起点
   - 应收欠款 = 期初欠款 + 新增订单欠款 - 收款 - 退货
   - 修改期初欠款会同步调整应收欠款

2. **储值与欠款的关系**:
   - 储值是客户预付的钱,可用于抵扣订单
   - 储值不影响应收欠款的计算
   - 使用储值抵扣订单时,会减少订单的实际欠款

3. **时间戳的重要性**:
   - 每次修改期初欠款或储值都会更新对应的时间戳
   - 时间戳用于对账单的时间排序
   - 输入0或留空会清除时间戳

4. **数据一致性**:
   - 后端会自动验证数据的合法性
   - 期初欠款和储值不能为负数
   - 修改期初欠款不能导致应收欠款小于0

## 测试建议

1. **功能测试**:
   - 新增客户时录入期初欠款和储值
   - 修改客户的期初欠款(增加、减少、清零)
   - 修改客户的储值(增加、减少、清零)
   - 查看对账单,验证记录显示和排序

2. **边界测试**:
   - 输入0测试
   - 输入负数测试(应该被阻止或自动转为0)
   - 输入非常大的数字
   - 留空测试

3. **排序测试**:
   - 创建多条不同日期的记录
   - 测试升序和降序排序
   - 验证相同日期的记录按ID排序

## 文件修改清单

### 后端文件
- ✅ `backend/routes/customers.py` - 客户API接口逻辑
- ✅ `backend/utils/db.py` - 数据库schema定义
- ✅ `backend/utils/db_helper.py` - 数据库读写辅助函数

### 前端文件
- ✅ `src/views/admin/customers/CustomerList.vue` - 客户列表和编辑界面
- ✅ `src/views/admin/finance/DebtDetails.vue` - 客户对账单界面

## 总结

本次优化完成了以下功能:
1. ✅ 客户数据增加了储值和期初欠款两个字段及时间戳
2. ✅ 编辑客户时可以修改储值和期初欠款
3. ✅ 输入0或留空时会删除对应的数据
4. ✅ 修改时自动更新时间戳
5. ✅ 对账单中显示期初欠款和储值记录
6. ✅ 对账单按时间排序,时间近的在上面
7. ✅ 期初欠款和储值有特殊的视觉标识(颜色标签)

系统现在可以完整地管理客户的财务信息,包括历史欠款、储值、订单欠款和收款记录。
