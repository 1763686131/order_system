import express from 'express'
import cors from 'cors'
import bodyParser from 'body-parser'
import fs from 'fs/promises'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

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
const storesDbPath = path.join(__dirname, 'data/stores_db.json')
const freightDbPath = path.join(__dirname, 'data/freight_records_db.json')

// ==================== 辅助函数 ====================

// 读取门店数据库
async function readStoresDB() {
  try {
    const data = await fs.readFile(storesDbPath, 'utf8')
    return JSON.parse(data)
  } catch (error) {
    if (error.code === 'ENOENT') {
      const initialData = [
        { id: 1, code: 'insulation', name: '绝缘', status: 'active', remark: '绝缘材料门店', created_at: new Date().toISOString().split('T')[0] },
        { id: 2, code: 'zhonggu', name: '中固', status: 'active', remark: '中固材料门店', created_at: new Date().toISOString().split('T')[0] }
      ]
      await fs.writeFile(storesDbPath, JSON.stringify(initialData, null, 2))
      return initialData
    }
    return []
  }
}

// 写入门店数据库
async function writeStoresDB(data) {
  await fs.writeFile(storesDbPath, JSON.stringify(data, null, 2), 'utf8')
}

// 生成门店ID
function generateStoreId(stores) {
  if (stores.length === 0) return 1
  const maxId = Math.max(...stores.map(s => s.id))
  return maxId + 1
}

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

// 获取所有门店
app.get('/api/stores', async (req, res) => {
  try {
    const stores = await readStoresDB()
    res.json(stores)
  } catch (error) {
    console.error('获取门店列表失败:', error)
    res.status(500).json({ error: '获取门店列表失败' })
  }
})

// 获取单个门店
app.get('/api/stores/:id', async (req, res) => {
  try {
    const stores = await readStoresDB()
    const store = stores.find(s => s.id === parseInt(req.params.id))
    if (!store) {
      return res.status(404).json({ error: '门店不存在' })
    }
    res.json(store)
  } catch (error) {
    console.error('获取门店信息失败:', error)
    res.status(500).json({ error: '获取门店信息失败' })
  }
})

// 创建门店
app.post('/api/stores', async (req, res) => {
  try {
    const stores = await readStoresDB()
    const { code, name, status, remark } = req.body

    if (!code || !name) {
      return res.status(400).json({ error: '门店编码和名称不能为空' })
    }

    const existingStore = stores.find(s => s.code === code)
    if (existingStore) {
      return res.status(400).json({ error: '门店编码已存在' })
    }

    const newStore = {
      id: generateStoreId(stores),
      code: code.trim(),
      name: name.trim(),
      status: status || 'active',
      remark: remark || '',
      created_at: new Date().toISOString().split('T')[0]
    }

    stores.push(newStore)
    await writeStoresDB(stores)

    res.json({ success: true, store: newStore })
  } catch (error) {
    console.error('创建门店失败:', error)
    res.status(500).json({ error: '创建门店失败' })
  }
})

// 更新门店
app.put('/api/stores/:id', async (req, res) => {
  try {
    const stores = await readStoresDB()
    const storeId = parseInt(req.params.id)
    const { code, name, status, remark } = req.body

    const storeIndex = stores.findIndex(s => s.id === storeId)
    if (storeIndex === -1) {
      return res.status(404).json({ error: '门店不存在' })
    }

    if (!name) {
      return res.status(400).json({ error: '门店名称不能为空' })
    }

    if (code && code !== stores[storeIndex].code) {
      const existingStore = stores.find(s => s.code === code && s.id !== storeId)
      if (existingStore) {
        return res.status(400).json({ error: '门店编码已存在' })
      }
    }

    stores[storeIndex] = {
      ...stores[storeIndex],
      name: name.trim(),
      status: status || stores[storeIndex].status,
      remark: remark || '',
      updated_at: new Date().toISOString().split('T')[0]
    }

    if (code && code !== stores[storeIndex].code) {
      stores[storeIndex].code = code.trim()
    }

    await writeStoresDB(stores)

    res.json({ success: true, store: stores[storeIndex] })
  } catch (error) {
    console.error('更新门店失败:', error)
    res.status(500).json({ error: '更新门店失败' })
  }
})

// 删除门店
app.delete('/api/stores/:id', async (req, res) => {
  try {
    const stores = await readStoresDB()
    const storeId = parseInt(req.params.id)

    const storeIndex = stores.findIndex(s => s.id === storeId)
    if (storeIndex === -1) {
      return res.status(404).json({ error: '门店不存在' })
    }

    stores.splice(storeIndex, 1)
    await writeStoresDB(stores)

    res.json({ success: true, message: '删除成功' })
  } catch (error) {
    console.error('删除门店失败:', error)
    res.status(500).json({ error: '删除门店失败' })
  }
})

// ==================== 运费记录API ====================

// 读取运费记录数据库
async function readFreightDB() {
  try {
    const data = await fs.readFile(freightDbPath, 'utf8')
    return JSON.parse(data)
  } catch (error) {
    if (error.code === 'ENOENT') {
      const initialData = { freight_records: [], reserve_funds: [] }
      await fs.writeFile(freightDbPath, JSON.stringify(initialData, null, 2))
      return initialData
    }
    return { freight_records: [], reserve_funds: [] }
  }
}

// 写入运费记录数据库
async function writeFreightDB(data) {
  await fs.writeFile(freightDbPath, JSON.stringify(data, null, 2), 'utf8')
}

// 生成ID
function generateId() {
  return Date.now() + Math.random().toString(36).substr(2, 9)
}

app.get('/api/freight-records', async (req, res) => {
  try {
    const db = await readFreightDB()
    res.json(db.freight_records || [])
  } catch (error) {
    res.status(500).json({ error: '获取运费记录失败' })
  }
})

app.post('/api/freight-records', async (req, res) => {
  try {
    const db = await readFreightDB()
    const { type, year, month, period, orders, totalAmount, reserveFund } = req.body

    const record = {
      id: generateId(),
      type,
      year,
      month,
      period,
      orders,
      totalAmount,
      reserveFund,
      createdAt: new Date().toISOString(),
      createdBy: req.user?.username || '管理员'
    }

    db.freight_records.push(record)
    await writeFreightDB(db)

    res.json({ success: true, record })
  } catch (error) {
    console.error('创建运费记录失败:', error)
    res.status(500).json({ error: '创建运费记录失败' })
  }
})

app.get('/api/freight-records/reserve-fund', async (req, res) => {
  try {
    const db = await readFreightDB()
    const { type, startDate, endDate } = req.query

    let funds = db.reserve_funds || []

    if (type) {
      funds = funds.filter(f => f.type === type)
    }

    if (startDate && endDate) {
      funds = funds.filter(f => {
        const fundDate = f.date || ''
        return fundDate >= startDate && fundDate <= endDate
      })
    }

    res.json(funds)
  } catch (error) {
    res.status(500).json({ error: '获取备用金记录失败' })
  }
})

app.post('/api/freight-records/reserve-fund', async (req, res) => {
  try {
    const db = await readFreightDB()
    const { type, date, amount, note } = req.body

    const fund = {
      id: generateId(),
      type,
      date: date || new Date().toISOString().split('T')[0],
      amount: parseFloat(amount),
      note: note || '',
      createdAt: new Date().toISOString(),
      createdBy: req.user?.username || '管理员'
    }

    db.reserve_funds.push(fund)
    await writeFreightDB(db)

    res.json({ success: true, fund })
  } catch (error) {
    console.error('录入备用金失败:', error)
    res.status(500).json({ error: '录入备用金失败' })
  }
})

app.get('/api/freight-records/reserve-fund/latest', async (req, res) => {
  try {
    const { type } = req.query
    const db = await readFreightDB()

    const funds = db.reserve_funds.filter(f => f.type === type)

    if (funds.length === 0) {
      return res.json({ balance: 0 })
    }

    const balance = funds.reduce((sum, fund) => sum + fund.amount, 0)

    res.json({ balance })
  } catch (error) {
    console.error('获取备用金余额失败:', error)
    res.status(500).json({ error: '获取备用金余额失败' })
  }
})

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

export default app
