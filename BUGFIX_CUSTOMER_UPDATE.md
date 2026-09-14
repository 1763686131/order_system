# 客户修改功能Bug修复

## 问题描述

修改客户的期初欠款或储值时，后端报错：
```
sqlite3.InterfaceError: Error binding parameter 10 - probably unsupported type.
```

## 问题分析

### 问题1: 前端传递了id字段导致selectedCustomer为null
**现象**: 点击修改按钮后，`handleSubmit` 函数中访问 `selectedCustomer.value.id` 时报错 `Cannot read properties of null (reading 'id')`

**原因**: 
- `handleEdit` 函数调用 `closeDetailModal()`
- `closeDetailModal()` 将 `selectedCustomer.value` 设置为 `null`
- 之后 `handleSubmit` 无法获取客户ID

**解决方案**:
- 在 `formData` 中添加 `id` 字段
- 在 `handleEdit` 中将客户ID保存到 `formData.value.id`
- 在 `handleSubmit` 中使用 `formData.value.id` 代替 `selectedCustomer.value.id`

### 问题2: SQLite参数类型错误
**现象**: 后端执行UPDATE语句时报 `Error binding parameter 10` 错误

**原因**:
1. `_amount` 函数返回的是 Python float 类型
2. `_debt_money` 函数返回的是 `Decimal` 类型
3. 在计算 `receivable` 时使用了 Decimal 运算
4. SQLite的参数绑定可能无法正确处理 Decimal 对象

**解决方案**:
- 在执行SQL前，显式将所有数值转换为 `float` 类型
- 创建临时变量 `balance_float`, `initial_receivable_float`, `receivable_float`
- 确保传递给SQLite的参数都是Python基本类型

## 修复内容

### 前端修改 (CustomerList.vue)

1. **添加id字段到formData**:
```javascript
const formData = ref({
  id: null,  // 新增
  customerName: '',
  customerCode: '',
  // ... 其他字段
})
```

2. **handleEdit中保存客户ID**:
```javascript
const handleEdit = (customer) => {
  formData.value = {
    id: customer.id,  // 保存ID
    customerName: customer.customerName,
    // ...
  }
}
```

3. **handleSubmit中使用formData.id**:
```javascript
const handleSubmit = async () => {
  if (isEditMode.value) {
    if (!formData.value.id) {
      alert('客户ID缺失，无法保存')
      return
    }
    await request({
      url: `/customers/${formData.value.id}`,  // 使用formData.id
      method: 'PUT',
      data: formData.value
    })
  }
}
```

4. **closeEditModal中重置表单**:
```javascript
const closeEditModal = () => {
  showEditModal.value = false
  isEditMode.value = false
  selectedCustomer.value = null
  // 重置表单数据
  formData.value = {
    id: null,
    customerName: '',
    // ...
  }
}
```

### 后端修改 (routes/customers.py)

1. **update_customer - 显式类型转换**:
```python
# 将Decimal转为float以避免SQLite绑定错误
balance_float = float(values['balance'])
initial_receivable_float = float(values['initial_receivable'])
receivable_float = float(receivable)

cursor.execute(
    '''UPDATE customers SET ... WHERE id = ?''',
    (
        values['customer_code'],
        # ...
        balance_float,  # 使用float变量
        balance_at,
        initial_receivable_float,  # 使用float变量
        initial_receivable_at,
        receivable_float,  # 使用float变量
        # ...
    )
)
```

2. **create_customer - 显式类型转换**:
```python
# 将数值转为float以避免SQLite绑定错误
balance_float = float(values['balance'])
initial_receivable_float = float(values['initial_receivable'])

cursor.execute(
    '''INSERT INTO customers (...) VALUES (?, ?, ...)''',
    (
        # ...
        balance_float,
        now if balance_float > 0 else None,
        initial_receivable_float,
        now if initial_receivable_float > 0 else None,
        initial_receivable_float,
        # ...
    )
)
```

## 测试步骤

### 1. 测试修改期初欠款
1. 在客户列表中点击某个客户的"编辑"按钮
2. 修改"期初欠款"为新值(如80.50)
3. 点击"保存"
4. 应该看到"保存成功"提示
5. 刷新页面，验证期初欠款已更新

### 2. 测试修改储值
1. 在客户列表中点击某个客户的"编辑"按钮
2. 修改"储值余额"为新值(如150.00)
3. 点击"保存"
4. 应该看到"保存成功"提示
5. 刷新页面，验证储值余额已更新

### 3. 测试清零期初欠款
1. 编辑客户，将"期初欠款"改为0
2. 点击"保存"
3. 验证期初欠款被清零，时间戳被清空

### 4. 测试清零储值
1. 编辑客户，将"储值余额"改为0
2. 点击"保存"
3. 验证储值被清零，时间戳被清空

### 5. 测试应收欠款重新计算
1. 创建一个客户，期初欠款设为50元
2. 创建一个订单，欠款100元(总应收=150元)
3. 修改客户的期初欠款为80元
4. 验证总应收欠款变为180元(80+100)

## 注意事项

1. **类型转换的重要性**:
   - Python的 `Decimal` 类型虽然精确，但SQLite不一定能正确处理
   - 在执行SQL前，始终将数值转换为 `float` 类型
   - 使用临时变量存储转换后的值，提高代码可读性

2. **formData中的id字段**:
   - 新增时 `id` 为 `null`
   - 编辑时 `id` 为客户的实际ID
   - 关闭编辑弹窗时要重置 `id` 为 `null`

3. **时间戳处理**:
   - 当值大于0时，设置时间戳为当前时间
   - 当值为0或空时，时间戳设为 `None`
   - SQLite会正确处理 `None` 值为 `NULL`

4. **应收欠款的自动计算**:
   - 修改期初欠款会自动调整应收欠款
   - 公式: 新应收 = 旧应收 - 旧期初 + 新期初
   - 必须验证新应收不能小于0

## 涉及文件

### 前端
- ✅ `src/views/admin/customers/CustomerList.vue` (修改)

### 后端
- ✅ `backend/routes/customers.py` (修改)

## 修复结果

- ✅ 修复前端ID缺失问题
- ✅ 修复SQLite参数类型绑定错误
- ✅ 确保数值类型正确转换
- ✅ 保持代码逻辑清晰可维护

现在可以正常修改客户的期初欠款和储值了！
