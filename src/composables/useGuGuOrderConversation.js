import { computed, ref } from 'vue'

const sameId = (left, right) => String(left) === String(right)
const normalize = value => String(value || '').trim().toLowerCase().replace(/[\s（）()·-]/g, '')
const positive = value => value !== '' && value != null && Number.isFinite(Number(value)) && Number(value) > 0
const normalizeUnit = value => {
  const unit = normalize(value)
  if (['公斤', '千克', 'kg', 'kgs'].includes(unit)) return 'kg'
  if (['吨', 't', 'ton'].includes(unit)) return 't'
  if (['克', 'g'].includes(unit)) return 'g'
  return unit
}
const numberReply = text => {
  const match = String(text).trim().match(/^(?:(?:确认|一共|总共|共|改成|改为|数量为|数量是|件数为|件数是)\s*)?((?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)\s*([a-zA-Z\u4e00-\u9fff]*)$/)
  if (!match) return null
  const value = Number(match[1].replaceAll(',', ''))
  return positive(value) ? { value, unit: match[2] } : null
}

export const looksLikeGuGuOrderRequest = text => {
  if (/查询|查一下|查找|统计|多少订单|订单多少|查订单/.test(text)) return false
  const hasQuantity = /\d+(?:\.\d+)?\s*(公斤|千克|kg|吨|桶|箱|件)/i.test(text)
  const isCustomerDelivery = /给.{1,20}(?:发|寄|送)|(?:发|寄|送)给.{1,20}/.test(text)
  return /(?:新增|新建|录入|创建|整理|生成|做一?张|开一?张).{0,8}(?:订单|销售单)|客户下单|帮我做单|帮我录单/.test(text) ||
    (hasQuantity && (/\b1[3-9]\d{9}\b/.test(text) ||
      /(?:胶|商品|收货|下单|送到)/.test(text) || isCustomerDelivery))
}

export function useGuGuOrderConversation({ messages, request, openOrder, onConfigurationError }) {
  const active = ref(false)
  const busy = ref(false)
  const opening = ref(false)
  const activeQuestionId = ref(0)
  const draft = ref(null)
  const catalogue = ref({ stores: [], warehouses: [], customers: [], products: [], units: [] })
  let sequence = 0
  let controller
  let sourceText = ''

  const currentQuestion = computed(() => messages.value.find(message =>
    message.orderFlow && message.id === activeQuestionId.value
  ))
  const stores = computed(() => catalogue.value.stores)
  const warehouses = computed(() => catalogue.value.warehouses.filter(warehouse =>
    sameId(warehouse.storeId ?? warehouse.store_id, draft.value?.storeId)
  ))
  const customers = computed(() => catalogue.value.customers.filter(customer =>
    sameId(customer.storeId, draft.value?.storeId)
  ))
  const products = computed(() => catalogue.value.products.filter(product =>
    Array.isArray(product.storeIds) && product.storeIds.some(id => sameId(id, draft.value?.storeId)) &&
    (!product.warehouseId || sameId(product.warehouseId, draft.value?.warehouseId))
  ))
  const productUnit = product => catalogue.value.units.find(unit => sameId(unit.id, product?.unitId))?.name || ''
  const productConversion = product => {
    const conversion = (Array.isArray(product?.unitConversions) ? product.unitConversions : [])
      .map(entry => ({
        unit: catalogue.value.units.find(unit => sameId(unit.id, entry?.fromUnitId))?.name || '',
        rate: Number(entry?.value)
      }))
      .find(entry => entry.unit && positive(entry.rate))
    return conversion || null
  }
  const productLabel = product => [product?.name, product?.specification || product?.spec, product?.code].filter(Boolean).join(' · ')
  const selectedProduct = item => products.value.find(product => sameId(product.id, item.productId))
  const itemComplete = item => Boolean(selectedProduct(item) && item.unit && item.modelConfirmed &&
    item.packagesConfirmed && item.quantityConfirmed && positive(item.packages) && positive(item.quantity))

  const say = (content, extra = {}) => {
    const message = { id: ++sequence, role: 'assistant', content, orderFlow: true, ...extra }
    messages.value.push(message)
    return message
  }
  const userReply = content => messages.value.push({
    id: ++sequence, role: 'user', content, orderFlow: true
  })
  const ask = (content, question, options = [], extra = {}) => {
    const message = say(content, { question, options, ...extra })
    activeQuestionId.value = message.id
    return message
  }
  const choices = (records, label) => records.map(record => ({
    key: String(record.id), value: record.id, label: label(record)
  }))
  const matchingProduct = (product, item) => {
    const name = normalize(item.name)
    const productName = normalize(product.name)
    return Boolean(name && productName &&
      (productName.includes(name) || name.includes(productName)))
  }
  const candidateProducts = item => {
    const matches = products.value.filter(product => matchingProduct(product, item))
    const spec = normalize(item.sourceSpec)
    return [...matches].sort((left, right) =>
      Number(normalize(right.specification || right.spec) === spec) -
      Number(normalize(left.specification || left.spec) === spec)
    )
  }
  const setCustomer = customer => {
    draft.value.customerId = customer.id
    for (const [field, value] of Object.entries({
      contactPerson: customer.contactPerson, contactPhone: customer.phone, contactAddress: customer.address
    })) {
      if (!draft.value[field]) draft.value[field] = value || ''
    }
  }
  const customerLabel = customer => customer.customerName || customer.name || ''
  const findCustomerMatches = () => {
    const rawHint = String(draft.value?.customerName || '')
    const hintVariants = [...new Set([
      rawHint,
      rawHint.replace(/^(?:(?:帮我|请|要)?(?:给|向|找|联系))/, '')
        .replace(/(?:发货|发|寄出|寄|送货|送|下单|要)+$/, '')
    ].map(normalize).filter(Boolean))]
    const source = normalize(sourceText)
    return customers.value
      .filter(customer => {
        const name = normalize(customerLabel(customer))
        const code = normalize(customer.customerCode || customer.code)
        return hintVariants.some(hint => name.includes(hint) || (code && code.includes(hint))) ||
          (name.length >= 2 && source.includes(name))
      })
      .sort((left, right) =>
        Number(hintVariants.includes(normalize(customerLabel(right)))) -
        Number(hintVariants.includes(normalize(customerLabel(left))))
      )
  }
  const askCustomerSelection = (prefix = '', includeMatches = true) => {
    const matches = includeMatches ? findCustomerMatches() : []
    if (matches.length > 1) {
      ask(
        `${prefix}找到多个可能的客户，请确认具体客户${draft.value.customerName ? `（原文提到“${draft.value.customerName}”）` : ''}。`,
        { type: 'customer', candidateIds: matches.map(customer => customer.id) },
        [...choices(matches, customerLabel), { key: 'other', label: '以上都不是' }]
      )
      return
    }
    ask(
      `${prefix}请选择系统中的客户${draft.value.customerName ? `，原文提到“${draft.value.customerName}”，也可以直接输入简称搜索` : ''}。`,
      { type: 'customer' },
      choices(customers.value, customerLabel)
    )
  }
  const askCustomerConfirmation = () => {
    const matches = findCustomerMatches()
    const storeName = stores.value.find(store => sameId(store.id, draft.value.storeId))?.name || '所选门店'
    if (matches.length === 1) {
      const customer = matches[0]
      ask(
        `在“${storeName}”下，您说的“${draft.value.customerName || customerLabel(customer)}”是客户“${customerLabel(customer)}”吗？`,
        { type: 'customer-confirm', customerId: customer.id },
        [{ key: 'yes', label: '是' }, { key: 'other', label: '不是，重新选择' }]
      )
      return
    }
    if (matches.length > 1) {
      ask(
        `在“${storeName}”下，原文中的“${draft.value.customerName}”可能对应多个客户，请选择。`,
        { type: 'customer', candidateIds: matches.map(customer => customer.id) },
        [...choices(matches, customerLabel), { key: 'other', label: '以上都不是' }]
      )
      return
    }
    askCustomerSelection(`在“${storeName}”下没有找到与“${draft.value.customerName || '原文客户信息'}”完全匹配的客户。`)
  }
  const resetProductConfirmation = item => {
    const hadInferredPackages = Boolean(item.packageConversion)
    item.productId = ''
    item.modelConfirmed = false
    item.packagesConfirmed = false
    item.quantityConfirmed = false
    if (hadInferredPackages) item.packages = ''
    item.packageConversion = null
    item.announced = false
  }

  const makeSummary = () => ({
    storeId: draft.value.storeId,
    storeName: stores.value.find(store => sameId(store.id, draft.value.storeId))?.name || '',
    warehouseId: draft.value.warehouseId,
    warehouseName: warehouses.value.find(warehouse => sameId(warehouse.id, draft.value.warehouseId))?.name || '',
    customerId: draft.value.customerId,
    customerName: customers.value.find(customer => sameId(customer.id, draft.value.customerId))?.customerName ||
      customers.value.find(customer => sameId(customer.id, draft.value.customerId))?.name || '',
    contactPerson: draft.value.contactPerson,
    contactPhone: draft.value.contactPhone,
    contactAddress: draft.value.contactAddress,
    projectName: draft.value.projectName,
    orderRemark: draft.value.remark,
    items: draft.value.items.map(item => ({
      productId: item.productId,
      label: productLabel(selectedProduct(item)),
      packages: Number(item.packages),
      quantity: Number(item.quantity),
      unit: item.unit,
      remark: item.notes || ''
    }))
  })

  const askProduct = (itemIndex, candidates = candidateProducts(draft.value.items[itemIndex])) => {
    const item = draft.value.items[itemIndex]
    const optionList = choices(candidates, productLabel)
    ask(
      optionList.length
        ? `请确认第 ${itemIndex + 1} 项“${item.name}”的具体型号${item.sourceSpec ? `，原文识别为“${item.sourceSpec}”` : ''}。`
        : `当前门店和仓库没有匹配到“${item.name}”，请回复更准确的商品名称或型号。`,
      { type: 'product', itemIndex, candidateIds: candidates.map(product => product.id) },
      optionList.slice(0, 16)
    )
  }
  const askNumber = (itemIndex, field, forceInput = false, prefix = '') => {
    const item = draft.value.items[itemIndex]
    const label = field === 'packages' ? '件数' : '数量'
    const conversion = field === 'packages' ? item.packageConversion : null
    const unit = field === 'packages' ? (conversion?.unit || '件') : item.unit
    const hasValue = positive(item[field])
    const suggestion = conversion && hasValue
      ? `按商品规格换算：1${conversion.unit}=${conversion.rate}${item.unit}，${item.quantity}${item.unit}可换算为${item.packages}${conversion.unit}。`
      : ''
    ask(
      `${prefix}${suggestion ? `${suggestion} ` : ''}第 ${itemIndex + 1} 项“${productLabel(selectedProduct(item))}”${hasValue && !forceInput
        ? `识别为 ${item[field]} ${unit}，请确认${label}。`
        : `请填写${label}（${unit}）${field === 'packages' && positive(item.quantity) ? `，商品总数量是 ${item.quantity} ${item.unit}` : ''}。`}`,
      { type: 'number', itemIndex, field },
      hasValue && !forceInput ? [
        { key: 'confirm', label: `确认 ${item[field]} ${unit}` },
        { key: 'edit', label: `修改${label}` }
      ] : []
    )
  }
  const nextQuestion = () => {
    if (!draft.value) return
    if (!draft.value.storeId) {
      ask('请选择这张销售单所属的门店。', { type: 'store' }, choices(stores.value, store => store.name))
      if (!stores.value.length) say('当前账号没有可用门店，请先完善门店资料或联系管理员。')
      return
    }
    if (!draft.value.customerId) {
      const customerMatches = findCustomerMatches()
      if (draft.value.customerName || customerMatches.length) askCustomerConfirmation()
      else askCustomerSelection('我暂时没有从原文识别出明确客户，')
      if (!customers.value.length) say('当前门店没有可用客户，请先添加客户资料。')
      return
    }
    if (!draft.value.warehouseId) {
      if (warehouses.value.length === 1) draft.value.warehouseId = warehouses.value[0].id
      else {
        ask('请选择本次出货仓库。', { type: 'warehouse' }, choices(warehouses.value, warehouse => warehouse.name))
        if (!warehouses.value.length) say('当前门店没有可用仓库，请先完善仓库资料。')
        return
      }
    }
    for (const [itemIndex, item] of draft.value.items.entries()) {
      if (!item.modelConfirmed || !selectedProduct(item)) {
        askProduct(itemIndex)
        return
      }
      if (!item.unit) {
        askProduct(itemIndex)
        say('该商品没有设置计量单位，请先完善商品资料，或选择其他商品。')
        return
      }
      if (!positive(item.quantity)) {
        askNumber(itemIndex, 'quantity', true, item.unitMismatch ? `原文单位为“${item.quantityUnit}”，该商品单位为“${item.unit}”。` : '')
        return
      }
      if (!item.packagesConfirmed) {
        askNumber(itemIndex, 'packages')
        return
      }
      if (!item.quantityConfirmed) {
        askNumber(itemIndex, 'quantity')
        return
      }
      if (!item.announced) {
        say(`第 ${itemIndex + 1} 项已确认：${productLabel(selectedProduct(item))}，${item.packages} 件，${item.quantity} ${item.unit}。`)
        item.announced = true
      }
    }
    for (const [field, label] of [
      ['contactPerson', '收货人姓名'], ['contactPhone', '收货人联系电话'], ['contactAddress', '收货地址，客户自提可回复“自提”']
    ]) {
      if (!draft.value[field]) {
        ask(`请补充${label}。`, { type: 'contact', field })
        return
      }
    }
    ask('信息已整理好，请检查订单摘要。地址、收货人、电话、项目或备注可以直接说“收货地址要修改一下”或“收货地址改成……”；商品型号、数量和件数可按序号修改。',
      { type: 'summary' }, [], { summary: makeSummary() })
  }

  const chooseProduct = (itemIndex, product) => {
    const item = draft.value.items[itemIndex]
    resetProductConfirmation(item)
    item.productId = product.id
    item.modelConfirmed = true
    item.unit = productUnit(product)
    item.unitMismatch = Boolean(item.quantityUnit && normalizeUnit(item.quantityUnit) !== normalizeUnit(item.unit))
    if (item.unitMismatch) item.quantity = ''
    const conversion = productConversion(product)
    if (!positive(item.packages) && positive(item.quantity) && conversion) {
      const inferredPackages = Number(item.quantity) / conversion.rate
      if (Number.isInteger(inferredPackages) && inferredPackages > 0) {
        item.packages = inferredPackages
        item.packageConversion = conversion
      }
    }
    nextQuestion()
  }
  const chooseScope = (type, record) => {
    if (type === 'customer') setCustomer(record)
    else {
      draft.value[`${type}Id`] = record.id
      if (type === 'store') {
        draft.value.warehouseId = ''
        draft.value.customerId = ''
      }
      draft.value.items.forEach(resetProductConfirmation)
    }
    nextQuestion()
  }
  const recordNumber = (itemIndex, field, text) => {
    const item = draft.value.items[itemIndex]
    const parsed = numberReply(text)
    const packageUnit = item.packageConversion?.unit
    const validUnit = !parsed?.unit || (field === 'packages'
      ? ['件', '桶', '箱', '包', '套', '个'].includes(parsed.unit) ||
        normalize(parsed.unit) === normalize(packageUnit)
      : normalizeUnit(parsed.unit) === normalizeUnit(item.unit))
    if (!parsed || !validUnit) {
      askNumber(itemIndex, field, true, `请回复大于 0 的数字${field === 'packages' ? '件数，例如“50件”' : `，单位为“${item.unit}”`}。`)
      return
    }
    item[field] = parsed.value
    item[`${field}Confirmed`] = true
    item.announced = false
    if (field === 'quantity') {
      item.quantityUnit = item.unit
      item.unitMismatch = false
      if (item.packageConversion) {
        const conversion = productConversion(selectedProduct(item))
        const inferredPackages = conversion ? Number(item.quantity) / conversion.rate : 0
        if (conversion && Number.isInteger(inferredPackages) && inferredPackages > 0) {
          item.packages = inferredPackages
          item.packagesConfirmed = false
          item.packageConversion = conversion
        } else {
          item.packages = ''
          item.packagesConfirmed = false
          item.packageConversion = null
        }
      }
    } else {
      item.packageConversion = null
    }
    nextQuestion()
  }
  const findChoice = (records, text, label, option, aliases = () => []) => {
    if (option?.value != null) return records.find(record => sameId(record.id, option.value))
    const value = normalize(text.replace(/^(?:选择|选|就用|我要|用)\s*/, ''))
    const exact = records.filter(record => [label(record), ...aliases(record)].filter(Boolean)
      .some(alias => normalize(alias) === value))
    if (exact.length === 1) return exact[0]
    const partial = records.filter(record => normalize(label(record)).includes(value))
    return partial.length === 1 ? partial[0] : null
  }

  const parseSource = async text => {
    sourceText = text
    const operation = new AbortController()
    controller = operation
    busy.value = true
    activeQuestionId.value = 0
    try {
      const signal = operation.signal
      const [parsed, ...lists] = await Promise.all([
        request.post('/ai/order-draft', { text }, { timeout: 75000, signal }),
        ...['/stores', '/warehouses', '/customers', '/products/inventory', '/products/units/measurements', '/products/units/packagings']
          .map(url => request.get(url, { signal }))
      ])
      if (signal.aborted || controller !== operation) return
      if (!parsed.success || !parsed.data?.draft?.items?.length || parsed.data.truncated) {
        throw Object.assign(new Error(parsed.message || '订单解析结果不完整，请补充或缩短下单内容后重试。'),
          { apiCode: parsed.code })
      }
      if (!lists.every(Array.isArray)) throw new Error('订单基础资料加载失败，请重试。')
      catalogue.value = {
        stores: lists[0],
        warehouses: lists[1],
        customers: lists[2],
        products: lists[3],
        units: [...lists[4], ...lists[5]]
      }
      const raw = parsed.data.draft
      draft.value = {
        ...raw, storeId: '', warehouseId: '', customerId: '',
        items: raw.items.map(item => ({
          ...item, sourceSpec: item.spec || '', quantityUnit: item.unit || '', productId: '',
          unit: '', packages: item.packages ?? '', quantity: item.quantity ?? '',
          modelConfirmed: false, packagesConfirmed: false, quantityConfirmed: false,
          packageConversion: null
        }))
      }
      say(`识别到 ${raw.items.length} 项商品${raw.contactPerson ? `，收货人为 ${raw.contactPerson}` : ''}。我会先确认门店和客户，再逐项核对商品。`)
      nextQuestion()
    } catch (error) {
      if (operation.signal.aborted || controller !== operation) return
      operation.abort()
      const message = error.response?.data?.message || error.message || '订单解析失败，请稍后重试。'
      ask(message, { type: 'source-retry' }, [{ key: 'retry', label: '重新分析原文' }])
      const code = error.response?.data?.code || error.apiCode
      if (['missing_api_key', 'invalid_api_key'].includes(code)) onConfigurationError?.(message)
    } finally {
      if (controller === operation) {
        controller = null
        busy.value = false
      }
    }
  }

  const normalizeContactValue = (value, field) => {
    const normalized = String(value || '').trim()
      .replace(/^(?:请)?(?:改成|改为|修改为|更改为|换成|改一下|修改一下|更改一下)\s*/, '')
    return field === 'contactAddress' && /^(自提|自取)$/.test(normalized) ? '客户自提' : normalized
  }
  const applyCorrection = text => {
    const detail = text.match(/^第\s*(\d+)\s*(?:项|条|个商品)?\s*(?:的)?\s*(型号|规格|件数|数量)\s*(?:改成|改为|修改为|换成|[:：])\s*(.+)$/)
    if (detail) {
      const index = Number(detail[1]) - 1
      const item = draft.value.items[index]
      if (!item) { say('没有这项商品，请按订单摘要中的序号修改。'); return true }
      if (detail[2] === '件数' || detail[2] === '数量') {
        recordNumber(index, detail[2] === '件数' ? 'packages' : 'quantity', detail[3])
      } else {
        const product = findChoice(candidateProducts(item), detail[3], productLabel, null,
          record => [record.specification || record.spec, record.code])
        if (product) chooseProduct(index, product)
        else askProduct(index)
      }
      return true
    }
    const fieldPattern = '(收货人|联系人|联系电话|电话|收货地址|地址|项目名称|项目|订单备注|备注)'
    const editIntent = text.match(new RegExp(`^(?:(?:请|麻烦)?(?:帮我)?|我(?:想|要)?)(?:把)?${fieldPattern}(?:信息)?(?:要|需要|想)?(?:修改|更改|改|换)(?:一下)?[。！!]*$`)) ||
      text.match(new RegExp(`^(?:(?:请|麻烦)?(?:帮我)?|我(?:想|要)?)(?:修改|更改|改|换)(?:一下)?(?:订单的)?${fieldPattern}(?:信息)?[。！!]*$`))
    if (editIntent) {
      const field = {
        收货人: 'contactPerson', 联系人: 'contactPerson', 联系电话: 'contactPhone', 电话: 'contactPhone',
        收货地址: 'contactAddress', 地址: 'contactAddress', 项目名称: 'projectName', 项目: 'projectName',
        订单备注: 'remark', 备注: 'remark'
      }[editIntent[1]]
      const labels = {
        contactPerson: '收货人姓名',
        contactPhone: '联系电话',
        contactAddress: '收货地址',
        projectName: '项目名称',
        remark: '订单备注'
      }
      ask(`好的，请告诉我新的${labels[field]}。`, { type: 'contact', field })
      return true
    }
    const header = text.match(/^(收货人|联系人|联系电话|电话|收货地址|地址|项目名称|项目|订单备注|备注|门店|仓库|客户)\s*(?:要|需要)?\s*(?:改成|改为|修改为|更改为|换成|[:：])\s*(.+)$/)
    if (!header) return false
    const field = {
      收货人: 'contactPerson', 联系人: 'contactPerson', 联系电话: 'contactPhone', 电话: 'contactPhone',
      收货地址: 'contactAddress', 地址: 'contactAddress', 项目名称: 'projectName', 项目: 'projectName',
      订单备注: 'remark', 备注: 'remark', 门店: 'store', 仓库: 'warehouse', 客户: 'customer'
    }[header[1]]
    if (['store', 'warehouse', 'customer'].includes(field)) {
      const records = field === 'store' ? stores.value : field === 'warehouse' ? warehouses.value : customers.value
      const record = findChoice(records, header[2], entry => entry.customerName || entry.name)
      if (record) chooseScope(field, record)
      else ask('请从当前可用资料中选择。', { type: field }, choices(records, entry => entry.customerName || entry.name))
    } else {
      draft.value[field] = normalizeContactValue(header[2], field)
      nextQuestion()
    }
    return true
  }

  const start = () => {
    const previous = currentQuestion.value
    active.value = true
    if (previous) ask(previous.content, previous.question, previous.options, previous.summary ? { summary: makeSummary() } : {})
    else ask('请把客户的下单文字发给我，我会确认型号、数量、件数和收货信息。', { type: 'source' })
  }
  const submit = async (text, option = null) => {
    const content = String(text || '').trim()
    if (!content || busy.value) return
    active.value = true
    userReply(content)
    if (/^(取消|取消这单|退出录单|退出订单整理|退出新增订单|返回聊天|返回日常聊天|切换到聊天|切换到日常聊天|普通聊天)$/.test(content)) {
      active.value = false
      activeQuestionId.value = 0
      draft.value = null
      sourceText = ''
      say('已退出新增订单整理，可以继续日常聊天；尚未创建订单。')
      return
    }
    if (/^(重新开始|重来|重新整理|换一单)$/.test(content)) {
      draft.value = null
      activeQuestionId.value = 0
      start()
      return
    }
    const message = currentQuestion.value
    const question = message?.question
    if (!question || ['source', 'source-retry'].includes(question.type)) {
      if (option?.key === 'retry' || (question?.type === 'source-retry' && /^(重试|重新分析|重新分析原文)$/.test(content))) {
        await parseSource(sourceText)
      } else if (/^(?:请|帮我|我要|我想|固固|GuGu|，|。|\s)*(?:新增|新建|创建|录入|整理|生成)(?:一张|一个)?(?:订单|销售单)[。！!，,\s]*$/i.test(content)) {
        ask('好的，把客户发来的商品、数量和收货信息贴给我。', { type: 'source' })
      } else await parseSource(content)
      return
    }
    if (draft.value && applyCorrection(content)) return
    if (question.type === 'customer-confirm') {
      const affirmative = option?.key === 'yes' ||
        /^(是|对|没错|正确|是的|好的|好|可以)$/.test(content)
      const negative = option?.key === 'other' ||
        /^(不是|不对|否|不是这个|换一个|重新选择)$/.test(content)
      const customer = customers.value.find(entry => sameId(entry.id, question.customerId))
      const replacement = !affirmative && !negative
        ? findChoice(customers.value, content, customerLabel)
        : null
      if (affirmative && customer) chooseScope('customer', customer)
      else if (negative) askCustomerSelection('好的，请重新选择客户。', false)
      else if (replacement) chooseScope('customer', replacement)
      else if (customer && findChoice([customer], content, customerLabel, option)) chooseScope('customer', customer)
      else ask(`请确认“${customerLabel(customer || {})}”是否为本次客户，或选择重新查找。`, question, message.options)
    } else if (['store', 'warehouse', 'customer'].includes(question.type)) {
      const allRecords = question.type === 'store' ? stores.value :
        question.type === 'warehouse' ? warehouses.value : customers.value
      const records = question.candidateIds
        ? allRecords.filter(entry => question.candidateIds.some(id => sameId(id, entry.id)))
        : allRecords
      if (question.type === 'customer' &&
        (option?.key === 'other' || /^(以上都不是|都不是|不是这些|重新选择)$/.test(content))) {
        askCustomerSelection('好的，请从当前门店的客户中重新选择。', false)
        return
      }
      const record = findChoice(records, content, question.type === 'customer' ? customerLabel : entry => entry.name, option)
      if (record) chooseScope(question.type, record)
      else ask('没有找到唯一匹配，请回复完整名称或选择下方选项。', question, message.options)
    } else if (question.type === 'product') {
      const item = draft.value.items[question.itemIndex]
      let candidates = products.value.filter(product => question.candidateIds.includes(product.id))
      let product = findChoice(candidates, content, productLabel, option, entry => [entry.specification || entry.spec, entry.code])
      if (!product && !option) {
        candidates = products.value.filter(entry => normalize(productLabel(entry)).includes(normalize(content)))
        if (candidates.length === 1) product = candidates[0]
      }
      if (product) chooseProduct(question.itemIndex, product)
      else askProduct(question.itemIndex, candidates.length ? candidates : candidateProducts(item))
    } else if (question.type === 'number') {
      const item = draft.value.items[question.itemIndex]
      if (option?.key === 'edit' || /^(修改|不对|不是|修改件数|修改数量)$/.test(content)) {
        item[`${question.field}Confirmed`] = false
        askNumber(question.itemIndex, question.field, true)
      } else if (positive(item[question.field]) && (option?.key === 'confirm' || /^(确认|对|是的|正确|没错|好的|好|可以)$/.test(content))) {
        item[`${question.field}Confirmed`] = true
        nextQuestion()
      } else recordNumber(question.itemIndex, question.field, content)
    } else if (question.type === 'contact') {
      draft.value[question.field] = normalizeContactValue(content, question.field)
      nextQuestion()
    } else if (question.type === 'summary') {
      say('可以直接说“收货地址要修改一下”，我会追问新地址；也可以说“收货地址改成……”直接更新。商品型号、数量和件数可按序号修改。')
    }
  }
  const answerOption = (message, option) => {
    if (!active.value || busy.value || message.id !== activeQuestionId.value || !message.options?.includes(option)) return
    return submit(option.label, option)
  }
  const confirmSummary = async message => {
    if (!active.value || busy.value || message.id !== activeQuestionId.value ||
      message.question?.type !== 'summary' || !draft.value?.items.length ||
      !draft.value.items.every(itemComplete)) return
    busy.value = true
    opening.value = true
    try {
      await openOrder(makeSummary())
      active.value = false
      activeQuestionId.value = 0
      say('已填充新增订单，请在订单页面检查并保存。')
    } catch (error) {
      say(error.message || '打开新增订单失败，可以重新点击确认按钮。')
    } finally {
      busy.value = false
      opening.value = false
    }
  }
  const cancel = () => {
    if (!controller) return
    controller.abort()
    controller = null
    busy.value = false
    ask('已停止分析。可以重新分析原文，或发来新的下单内容。', { type: 'source-retry' }, [{ key: 'retry', label: '重新分析原文' }])
  }
  const reset = () => {
    controller?.abort()
    controller = null
    active.value = false
    busy.value = false
    draft.value = null
    activeQuestionId.value = 0
    sourceText = ''
  }
  return { active, busy, opening, activeQuestionId, start, submit, answerOption, confirmSummary, cancel, reset }
}
