/**
 * 数据迁移脚本：将订单中的 type 字段迁移为 store_id
 * 执行方式：node scripts/migrate_order_type_to_store_id.js
 */

const fs = require('fs')
const path = require('path')

// 文件路径
const ORDERS_DB_PATH = path.join(__dirname, '../data/orders_db.json')
const BACKUP_PATH = path.join(__dirname, '../data/orders_db_backup_' + Date.now() + '.json')

// 迁移映射关系
const TYPE_TO_STORE_ID_MAP = {
  0: 2,  // type=0 (中固) -> store_id=2
  1: 1   // type=1 (绝缘) -> store_id=1
}

console.log('===== 开始数据迁移 =====\n')

try {
  // 1. 读取原始数据
  console.log('1. 读取订单数据...')
  const ordersData = fs.readFileSync(ORDERS_DB_PATH, 'utf8')
  const orders = JSON.parse(ordersData)
  console.log(`   共 ${orders.length} 条订单数据\n`)

  // 2. 备份原始数据
  console.log('2. 备份原始数据...')
  fs.writeFileSync(BACKUP_PATH, ordersData, 'utf8')
  console.log(`   备份文件：${BACKUP_PATH}\n`)

  // 3. 数据迁移
  console.log('3. 执行数据迁移...')
  let migratedCount = 0
  let skippedCount = 0

  orders.forEach((order, index) => {
    // 如果已经有 store_id，跳过
    if (order.store_id !== undefined) {
      skippedCount++
      return
    }

    // 根据 type 值设置 store_id
    if (order.type !== undefined) {
      order.store_id = TYPE_TO_STORE_ID_MAP[order.type] || 2 // 默认为中固
      migratedCount++
    } else {
      // 如果没有 type 字段，默认设置为中固
      order.store_id = 2
      migratedCount++
    }
  })

  console.log(`   迁移成功：${migratedCount} 条`)
  console.log(`   已跳过：${skippedCount} 条\n`)

  // 4. 保存迁移后的数据
  console.log('4. 保存迁移后的数据...')
  fs.writeFileSync(ORDERS_DB_PATH, JSON.stringify(orders, null, 2), 'utf8')
  console.log(`   数据已保存到：${ORDERS_DB_PATH}\n`)

  // 5. 显示迁移统计
  console.log('===== 迁移完成 =====')
  console.log(`总订单数：${orders.length}`)
  console.log(`已迁移：${migratedCount}`)
  console.log(`已跳过：${skippedCount}`)
  console.log('\n提示：')
  console.log('1. 原始数据已备份，如有问题可以恢复')
  console.log('2. 迁移后的数据保留了 type 字段，建议先测试确认无误后再删除')
  console.log('3. 如需删除 type 字段，请执行：node scripts/remove_type_field.js')

} catch (error) {
  console.error('❌ 迁移失败:', error.message)
  console.error(error)
  process.exit(1)
}
