const fs = require('fs').promises
const path = require('path')

const dbPath = path.join(__dirname, '../data/freight_records_db.json')

// 读取数据库
async function readDB() {
  try {
    const data = await fs.readFile(dbPath, 'utf8')
    return JSON.parse(data)
  } catch (error) {
    // 如果文件不存在，创建初始数据库
    if (error.code === 'ENOENT') {
      console.log('运费记录数据库不存在，正在创建...')
      const initialData = { freight_records: [], reserve_funds: [] }
      await writeDB(initialData)
      return initialData
    }
    console.error('读取运费记录数据库失败:', error)
    return { freight_records: [], reserve_funds: [] }
  }
}

// 写入数据库
async function writeDB(data) {
  try {
    await fs.writeFile(dbPath, JSON.stringify(data, null, 2), 'utf8')
    return true
  } catch (error) {
    console.error('写入运费记录数据库失败:', error)
    return false
  }
}

// 生成ID
function generateId() {
  return Date.now() + Math.random().toString(36).substr(2, 9)
}

// 获取所有运费记录
async function getFreightRecords(req, res) {
  try {
    const db = await readDB()
    res.json(db.freight_records || [])
  } catch (error) {
    res.status(500).json({ error: '获取运费记录失败' })
  }
}

// 创建运费记录（审核时）
async function createFreightRecord(req, res) {
  try {
    const db = await readDB()
    const { type, year, month, period, orders, totalAmount, reserveFund } = req.body

    const record = {
      id: generateId(),
      type, // 'logistics-truck' 或 'express-courier'
      year,
      month,
      period, // 物流/专车: '1-10', '11-20', '21-31'; 快运/快递: null
      orders, // 订单ID数组
      totalAmount, // 运费总额
      reserveFund, // 备用金余额
      createdAt: new Date().toISOString(),
      createdBy: req.user?.username || '管理员'
    }

    db.freight_records.push(record)
    await writeDB(db)

    res.json({ success: true, record })
  } catch (error) {
    console.error('创建运费记录失败:', error)
    res.status(500).json({ error: '创建运费记录失败' })
  }
}

// 获取所有备用金记录
async function getReserveFunds(req, res) {
  try {
    const db = await readDB()
    const { type, startDate, endDate } = req.query

    let funds = db.reserve_funds || []

    // 按类型筛选
    if (type) {
      funds = funds.filter(f => f.type === type)
    }

    // 按日期范围筛选
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
}

// 录入备用金
async function createReserveFund(req, res) {
  try {
    const db = await readDB()
    const { type, date, amount, note } = req.body

    const fund = {
      id: generateId(),
      type, // 'logistics-truck' 或 'express-courier'
      date: date || new Date().toISOString().split('T')[0], // 日期
      amount: parseFloat(amount),
      note: note || '',
      createdAt: new Date().toISOString(),
      createdBy: req.user?.username || '管理员'
    }

    db.reserve_funds.push(fund)
    await writeDB(db)

    res.json({ success: true, fund })
  } catch (error) {
    console.error('录入备用金失败:', error)
    res.status(500).json({ error: '录入备用金失败' })
  }
}

// 获取最新备用金余额
async function getLatestReserveFund(req, res) {
  try {
    const { type } = req.query
    const db = await readDB()

    // 筛选对应类型的备用金记录
    const funds = db.reserve_funds.filter(f => f.type === type)

    if (funds.length === 0) {
      return res.json({ balance: 0 })
    }

    // 计算总额
    const balance = funds.reduce((sum, fund) => sum + fund.amount, 0)

    res.json({ balance })
  } catch (error) {
    console.error('获取备用金余额失败:', error)
    res.status(500).json({ error: '获取备用金余额失败' })
  }
}

module.exports = {
  getFreightRecords,
  createFreightRecord,
  getReserveFunds,
  createReserveFund,
  getLatestReserveFund
}
