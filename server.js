const express = require('express')
const cors = require('cors')
const bodyParser = require('body-parser')
const fs = require('fs').promises
const path = require('path')

// 导入API模块
const storesAPI = require('./server/stores')
const freightRecordsAPI = require('./server/freightRecords')

const app = express()
const PORT = 7899

// 中间件
app.use(cors())
app.use(bodyParser.json())
app.use(bodyParser.urlencoded({ extended: true }))

// 用户信息中间件（从请求头获取用户名）
app.use((req, res, next) => {
  const username = req.headers['username']
  if (username) {
    req.user = { username: decodeURIComponent(username) }
  }
  next()
})

// 数据库路径
const ordersDbPath = path.join(__dirname, 'data/orders_db.json')
const materialsDbPath = path.join(__dirname, 'data/materials_db.json')

// ==================== 订单相关API ====================

// 获取所有订单
app.get('/api/orders', async (req, res) => {
  try {
    const data = await fs.readFile(ordersDbPath, 'utf8')
    const orders = JSON.parse(data)
    res.json(orders)
  } catch (error) {
    console.error('读取订单失败:', error)
    res.status(500).json({ error: '读取订单失败' })
  }
})

// 创建订单
app.post('/api/orders', async (req, res) => {
  try {
    const data = await fs.readFile(ordersDbPath, 'utf8')
    const orders = JSON.parse(data)

    const newOrder = {
      ...req.body,
      id: Date.now().toString()
    }

    orders.push(newOrder)
    await fs.writeFile(ordersDbPath, JSON.stringify(orders, null, 2))

    res.json(newOrder)
  } catch (error) {
    console.error('创建订单失败:', error)
    res.status(500).json({ error: '创建订单失败' })
  }
})

// 更新订单
app.put('/api/orders/:id', async (req, res) => {
  try {
    const data = await fs.readFile(ordersDbPath, 'utf8')
    const orders = JSON.parse(data)

    const index = orders.findIndex(o => o.id === req.params.id)
    if (index === -1) {
      return res.status(404).json({ error: '订单不存在' })
    }

    orders[index] = { ...orders[index], ...req.body }
    await fs.writeFile(ordersDbPath, JSON.stringify(orders, null, 2))

    res.json(orders[index])
  } catch (error) {
    console.error('更新订单失败:', error)
    res.status(500).json({ error: '更新订单失败' })
  }
})

// 更新订单已支付金额
app.put('/api/orders/:id/paid-amount', async (req, res) => {
  try {
    const { freightCostIndex, paidAmount } = req.body
    const data = await fs.readFile(ordersDbPath, 'utf8')
    const orders = JSON.parse(data)

    const order = orders.find(o => o.id === req.params.id)
    if (!order) {
      return res.status(404).json({ error: '订单不存在' })
    }

    if (order.freight_costs && order.freight_costs[freightCostIndex]) {
      order.freight_costs[freightCostIndex].paid_amount = paidAmount
      await fs.writeFile(ordersDbPath, JSON.stringify(orders, null, 2))
      res.json({ success: true })
    } else {
      res.status(400).json({ error: '运费记录不存在' })
    }
  } catch (error) {
    console.error('更新已支付金额失败:', error)
    res.status(500).json({ error: '更新已支付金额失败' })
  }
})

// 删除订单
app.delete('/api/orders/:id', async (req, res) => {
  try {
    const data = await fs.readFile(ordersDbPath, 'utf8')
    let orders = JSON.parse(data)

    orders = orders.filter(o => o.id !== req.params.id)
    await fs.writeFile(ordersDbPath, JSON.stringify(orders, null, 2))

    res.json({ success: true })
  } catch (error) {
    console.error('删除订单失败:', error)
    res.status(500).json({ error: '删除订单失败' })
  }
})

// ==================== 原材料相关API ====================

// 获取所有原材料
app.get('/api/materials', async (req, res) => {
  try {
    const data = await fs.readFile(materialsDbPath, 'utf8')
    const materials = JSON.parse(data)
    res.json(materials)
  } catch (error) {
    console.error('读取原材料失败:', error)
    res.status(500).json({ error: '读取原材料失败' })
  }
})

// 创建原材料
app.post('/api/materials', async (req, res) => {
  try {
    const data = await fs.readFile(materialsDbPath, 'utf8')
    const materials = JSON.parse(data)

    const newMaterial = {
      ...req.body,
      id: Date.now().toString()
    }

    materials.push(newMaterial)
    await fs.writeFile(materialsDbPath, JSON.stringify(materials, null, 2))

    res.json(newMaterial)
  } catch (error) {
    console.error('创建原材料失败:', error)
    res.status(500).json({ error: '创建原材料失败' })
  }
})

// ==================== 门店管理API ====================

app.get('/api/stores', storesAPI.getStores)
app.get('/api/stores/:id', storesAPI.getStoreById)
app.post('/api/stores', storesAPI.createStore)
app.put('/api/stores/:id', storesAPI.updateStore)
app.delete('/api/stores/:id', storesAPI.deleteStore)

// ==================== 运费记录API ====================

app.get('/api/freight-records', freightRecordsAPI.getFreightRecords)
app.post('/api/freight-records', freightRecordsAPI.createFreightRecord)
app.get('/api/freight-records/reserve-fund', freightRecordsAPI.getReserveFunds)
app.post('/api/freight-records/reserve-fund', freightRecordsAPI.createReserveFund)
app.get('/api/freight-records/reserve-fund/latest', freightRecordsAPI.getLatestReserveFund)

// 更新备用金金额
app.put('/api/freight-records/reserve-fund/:id', async (req, res) => {
  try {
    const freightDbPath = path.join(__dirname, 'data/freight_records_db.json')
    const data = await fs.readFile(freightDbPath, 'utf8')
    const db = JSON.parse(data)

    const fundIndex = db.reserve_funds.findIndex(f => f.id === req.params.id)
    if (fundIndex === -1) {
      return res.status(404).json({ error: '备用金记录不存在' })
    }

    db.reserve_funds[fundIndex].amount = parseFloat(req.body.amount)
    await fs.writeFile(freightDbPath, JSON.stringify(db, null, 2))

    res.json({ success: true })
  } catch (error) {
    console.error('更新备用金失败:', error)
    res.status(500).json({ error: '更新备用金失败' })
  }
})

// ==================== 健康检查 ====================

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', message: '服务运行正常' })
})

// ==================== 启动服务器 ====================

app.listen(PORT, () => {
  console.log(`========================================`)
  console.log(`  订单管理系统后端服务`)
  console.log(`  端口: ${PORT}`)
  console.log(`  时间: ${new Date().toLocaleString()}`)
  console.log(`========================================`)
  console.log(`  订单API: http://localhost:${PORT}/api/orders`)
  console.log(`  门店API: http://localhost:${PORT}/api/stores`)
  console.log(`  运费API: http://localhost:${PORT}/api/freight-records`)
  console.log(`========================================`)
})

module.exports = app
