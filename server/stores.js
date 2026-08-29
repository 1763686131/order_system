const fs = require('fs').promises
const path = require('path')

const dbPath = path.join(__dirname, '../data/stores_db.json')

// 读取数据库
async function readDB() {
  try {
    const data = await fs.readFile(dbPath, 'utf8')
    return JSON.parse(data)
  } catch (error) {
    // 如果文件不存在，创建初始数据库
    if (error.code === 'ENOENT') {
      console.log('门店数据库不存在，正在创建...')
      const initialData = [
        {
          id: 1,
          code: 'insulation',
          name: '绝缘',
          status: 'active',
          remark: '绝缘材料门店',
          created_at: new Date().toISOString().split('T')[0]
        },
        {
          id: 2,
          code: 'zhonggu',
          name: '中固',
          status: 'active',
          remark: '中固材料门店',
          created_at: new Date().toISOString().split('T')[0]
        }
      ]
      await writeDB(initialData)
      return initialData
    }
    console.error('读取门店数据库失败:', error)
    return []
  }
}

// 写入数据库
async function writeDB(data) {
  try {
    await fs.writeFile(dbPath, JSON.stringify(data, null, 2), 'utf8')
    return true
  } catch (error) {
    console.error('写入门店数据库失败:', error)
    return false
  }
}

// 生成ID
function generateId(stores) {
  if (stores.length === 0) return 1
  const maxId = Math.max(...stores.map(s => s.id))
  return maxId + 1
}

// 获取所有门店
async function getStores(req, res) {
  try {
    const stores = await readDB()
    res.json(stores)
  } catch (error) {
    res.status(500).json({ error: '获取门店列表失败' })
  }
}

// 获取单个门店
async function getStoreById(req, res) {
  try {
    const stores = await readDB()
    const store = stores.find(s => s.id === parseInt(req.params.id))

    if (!store) {
      return res.status(404).json({ error: '门店不存在' })
    }

    res.json(store)
  } catch (error) {
    res.status(500).json({ error: '获取门店信息失败' })
  }
}

// 创建门店
async function createStore(req, res) {
  try {
    const stores = await readDB()
    const { code, name, status, remark } = req.body

    // 验证必填字段
    if (!code || !name) {
      return res.status(400).json({ error: '门店编码和名称不能为空' })
    }

    // 检查编码是否重复
    const existingStore = stores.find(s => s.code === code)
    if (existingStore) {
      return res.status(400).json({ error: '门店编码已存在' })
    }

    // 创建新门店
    const newStore = {
      id: generateId(stores),
      code: code.trim(),
      name: name.trim(),
      status: status || 'active',
      remark: remark || '',
      created_at: new Date().toISOString().split('T')[0]
    }

    stores.push(newStore)
    await writeDB(stores)

    res.json({ success: true, store: newStore })
  } catch (error) {
    console.error('创建门店失败:', error)
    res.status(500).json({ error: '创建门店失败' })
  }
}

// 更新门店
async function updateStore(req, res) {
  try {
    const stores = await readDB()
    const storeId = parseInt(req.params.id)
    const { code, name, status, remark } = req.body

    const storeIndex = stores.findIndex(s => s.id === storeId)
    if (storeIndex === -1) {
      return res.status(404).json({ error: '门店不存在' })
    }

    // 验证必填字段
    if (!name) {
      return res.status(400).json({ error: '门店名称不能为空' })
    }

    // 如果修改编码，检查是否重复
    if (code && code !== stores[storeIndex].code) {
      const existingStore = stores.find(s => s.code === code && s.id !== storeId)
      if (existingStore) {
        return res.status(400).json({ error: '门店编码已存在' })
      }
    }

    // 更新门店信息（保留 id 和 created_at）
    stores[storeIndex] = {
      ...stores[storeIndex],
      name: name.trim(),
      status: status || stores[storeIndex].status,
      remark: remark || '',
      updated_at: new Date().toISOString().split('T')[0]
    }

    // 如果允许修改编码（注意：这可能影响关联数据）
    if (code && code !== stores[storeIndex].code) {
      stores[storeIndex].code = code.trim()
    }

    await writeDB(stores)

    res.json({ success: true, store: stores[storeIndex] })
  } catch (error) {
    console.error('更新门店失败:', error)
    res.status(500).json({ error: '更新门店失败' })
  }
}

// 删除门店
async function deleteStore(req, res) {
  try {
    const stores = await readDB()
    const storeId = parseInt(req.params.id)

    const storeIndex = stores.findIndex(s => s.id === storeId)
    if (storeIndex === -1) {
      return res.status(404).json({ error: '门店不存在' })
    }

    // TODO: 检查是否有关联的订单数据
    // 这里可以添加检查逻辑，确保删除前没有关联数据

    stores.splice(storeIndex, 1)
    await writeDB(stores)

    res.json({ success: true, message: '删除成功' })
  } catch (error) {
    console.error('删除门店失败:', error)
    res.status(500).json({ error: '删除门店失败' })
  }
}

// 根据 store_id 获取门店信息
async function getStoreByStoreId(storeId) {
  try {
    const stores = await readDB()
    return stores.find(s => s.id === storeId)
  } catch (error) {
    console.error('获取门店信息失败:', error)
    return null
  }
}

// 根据 code 获取门店信息
async function getStoreByCode(code) {
  try {
    const stores = await readDB()
    return stores.find(s => s.code === code)
  } catch (error) {
    console.error('获取门店信息失败:', error)
    return null
  }
}

module.exports = {
  getStores,
  getStoreById,
  createStore,
  updateStore,
  deleteStore,
  getStoreByStoreId,
  getStoreByCode
}
