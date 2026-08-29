/**
 * 清理脚本：删除订单数据中的 type 字段
 * 执行方式：node scripts/remove_type_field.js
 *
 * ⚠️ 警告：执行此脚本前，请确保已完成数据迁移并充分测试！
 */

const fs = require('fs')
const path = require('path')
const readline = require('readline')

// 文件路径
const ORDERS_DB_PATH = path.join(__dirname, '../data/orders_db.json')
const BACKUP_PATH = path.join(__dirname, '../data/orders_db_before_remove_type_' + Date.now() + '.json')

// 创建命令行交互
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
})

console.log('===== 删除 type 字段 =====\n')
console.log('⚠️  警告：此操作将永久删除订单数据中的 type 字段！')
console.log('请确保：')
console.log('1. 已执行数据迁移脚本')
console.log('2. 所有订单都已有 store_id 字段')
console.log('3. 系统已经测试通过，不再使用 type 字段\n')

rl.question('确认要继续吗？(输入 yes 继续): ', (answer) => {
  if (answer.toLowerCase() !== 'yes') {
    console.log('操作已取消')
    rl.close()
    return
  }

  try {
    // 1. 读取数据
    console.log('\n1. 读取订单数据...')
    const ordersData = fs.readFileSync(ORDERS_DB_PATH, 'utf8')
    const orders = JSON.parse(ordersData)
    console.log(`   共 ${orders.length} 条订单数据`)

    // 2. 检查 store_id 字段
    console.log('\n2. 检查数据完整性...')
    const missingStoreId = orders.filter(order => order.store_id === undefined)
    if (missingStoreId.length > 0) {
      console.error(`   ❌ 发现 ${missingStoreId.length} 条订单缺少 store_id 字段！`)
      console.error('   请先执行迁移脚本：node scripts/migrate_order_type_to_store_id.js')
      rl.close()
      return
    }
    console.log('   ✓ 所有订单都有 store_id 字段')

    // 3. 备份
    console.log('\n3. 备份原始数据...')
    fs.writeFileSync(BACKUP_PATH, ordersData, 'utf8')
    console.log(`   备份文件：${BACKUP_PATH}`)

    // 4. 删除 type 字段
    console.log('\n4. 删除 type 字段...')
    let removedCount = 0
    orders.forEach(order => {
      if (order.type !== undefined) {
        delete order.type
        removedCount++
      }
    })
    console.log(`   已删除 ${removedCount} 条订单的 type 字段`)

    // 5. 保存
    console.log('\n5. 保存数据...')
    fs.writeFileSync(ORDERS_DB_PATH, JSON.stringify(orders, null, 2), 'utf8')
    console.log(`   数据已保存到：${ORDERS_DB_PATH}`)

    console.log('\n===== 清理完成 =====')
    console.log(`删除了 ${removedCount} 个 type 字段`)
    console.log('原始数据已备份，如有问题可以恢复')

  } catch (error) {
    console.error('\n❌ 清理失败:', error.message)
    console.error(error)
  }

  rl.close()
})
