export const DEFAULT_LOGISTICS_COPY_FIELDS = [
  {
    key: 'title',
    name: '标题',
    template: '【@storeName订单】',
    enabled: true
  },
  {
    key: 'receiver_name',
    name: '姓名',
    variable: 'receiverName',
    template: '姓名：@receiverName',
    enabled: true
  },
  {
    key: 'receiver_phone',
    name: '电话',
    variable: 'receiverPhone',
    template: '电话：@receiverPhone',
    enabled: true
  },
  {
    key: 'receiver_address',
    name: '地址',
    variable: 'receiverAddress',
    template: '地址：@receiverAddress',
    enabled: true
  },
  {
    key: 'goods_name',
    name: '商品',
    variable: 'goodsName',
    template: '商品：@goodsName',
    enabled: true
  },
  {
    key: 'goods_weight',
    name: '重量',
    variable: 'goodsWeight',
    template: '重量：@goodsWeight',
    enabled: true
  },
  {
    key: 'goods_quantity',
    name: '件数',
    variable: 'goodsQuantity',
    template: '件数：@goodsQuantity',
    enabled: true
  },
  {
    key: 'goods_packaging',
    name: '包装',
    variable: 'goodsPackaging',
    template: '包装：@goodsPackaging',
    enabled: true
  },
  {
    key: 'logistics_service',
    name: '服务',
    variable: 'logisticsService',
    template: '服务：@logisticsService',
    enabled: true
  },
  {
    key: 'remark',
    name: '备注',
    variable: 'orderRemark',
    template: '备注：@orderRemark',
    enabled: true
  }
]

export const LOGISTICS_COPY_VARIABLE_GROUPS = [
  {
    id: 'order',
    label: '订单信息',
    variables: [
      { key: 'storeName', label: '门店名称' },
      { key: 'orderNumber', label: '订单编号' },
      { key: 'orderDate', label: '单据日期' },
      { key: 'customerName', label: '客户名称' },
      { key: 'warehouseName', label: '仓库名称' },
      { key: 'projectName', label: '工程项目' }
    ]
  },
  {
    id: 'receiver',
    label: '收货信息',
    variables: [
      { key: 'receiverName', label: '姓名' },
      { key: 'receiverPhone', label: '电话' },
      { key: 'receiverAddress', label: '地址' }
    ]
  },
  {
    id: 'contact',
    label: '联系人信息',
    variables: [
      { key: 'contactPerson', label: '联系人' },
      { key: 'contactPhone', label: '联系方式' },
      { key: 'contactAddress', label: '联系地址' }
    ]
  },
  {
    id: 'goods',
    label: '商品信息',
    variables: [
      { key: 'goodsName', label: '首件商品' },
      { key: 'spec', label: '首件规格' },
      { key: 'unit', label: '首件单位' },
      { key: 'allGoods', label: '全部商品' },
      { key: 'allSpecs', label: '全部规格' },
      { key: 'allQuantity', label: '全部数量' },
      { key: 'goodsWeight', label: '重量' },
      { key: 'goodsQuantity', label: '件数' },
      { key: 'totalQuantity', label: '合计数量' },
      { key: 'totalPackages', label: '合计件数' },
      { key: 'goodsPackaging', label: '包装' }
    ]
  },
  {
    id: 'logistics',
    label: '物流信息',
    variables: [
      { key: 'logisticsService', label: '服务' },
      { key: 'shippingMethod', label: '发货方式' },
      { key: 'logisticsNo', label: '物流单号' },
      { key: 'shippedDate', label: '发货日期' },
      { key: 'freightTotal', label: '运费' }
    ]
  },
  {
    id: 'other',
    label: '其他',
    variables: [
      { key: 'salesPerson', label: '业务员' },
      { key: 'creator', label: '制单人' },
      { key: 'orderRemark', label: '订单备注' },
      { key: 'discountAmount', label: '折扣金额' },
      { key: 'otherFees', label: '其他费用' },
      { key: 'totalAmount', label: '合计金额' },
      { key: 'totalTaxAmount', label: '含税金额' },
      { key: 'currentPayment', label: '本次收款' },
      { key: 'currentDebt', label: '本单欠款' },
      { key: 'settlementAccount', label: '结算账户' },
      { key: 'shouldReceive', label: '本单应收' },
      { key: 'amountInWords', label: '金额大写' },
      { key: 'orderRemark', label: '订单备注' }
    ]
  }
]

const DEFAULT_FIELD_MAP = new Map(
  DEFAULT_LOGISTICS_COPY_FIELDS.map(field => [field.key, field])
)

const cloneFields = fields => fields.map(field => ({ ...field }))

export const getDefaultLogisticsCopyFields = () => cloneFields(DEFAULT_LOGISTICS_COPY_FIELDS)

export const normalizeLogisticsCopyFields = fields => {
  if (!Array.isArray(fields)) {
    return getDefaultLogisticsCopyFields()
  }

  const normalized = []
  const seen = new Set()

  fields.forEach(field => {
    const fallback = DEFAULT_FIELD_MAP.get(field?.key)
    const isCustomField = String(field?.key || '').startsWith('custom_')
    if ((!fallback && !isCustomField) || seen.has(field?.key)) {
      return
    }

    if (isCustomField) {
      normalized.push({
        key: String(field.key),
        name: String(field.name || '自定义字段'),
        template: String(field.template || '').trim(),
        enabled: field.enabled !== false,
        custom: true
      })
      seen.add(field.key)
      return
    }

    normalized.push({
      key: fallback.key,
      name: fallback.name,
      template: String(
        field.template ||
        (
          field.label
            ? `${field.label}：@${fallback.variable || fallback.key}`
            : fallback.template
        )
      ).trim() || fallback.template,
      enabled: field.enabled !== false
    })
    seen.add(fallback.key)
  })

  return normalized
}

export const resolveLogisticsCopyFields = (
  templates,
  bindingTarget,
  userId,
  fallbackFields = getDefaultLogisticsCopyFields()
) => {
  const normalizedUserId = Number(userId)
  const matchedTemplate = Array.isArray(templates)
    ? templates.find(template => (
      template?.bindingTarget === bindingTarget &&
      Array.isArray(template.boundUserIds) &&
      template.boundUserIds.some(id => Number(id) === normalizedUserId)
    ))
    : null

  return matchedTemplate
    ? normalizeLogisticsCopyFields(matchedTemplate.fields)
    : normalizeLogisticsCopyFields(fallbackFields)
}

const getFirstGoods = order => (
  Array.isArray(order?.order_goods) && order.order_goods.length > 0
    ? order.order_goods[0]
    : null
)

const getGoodsItemName = item => String(
  item?.goods_name ||
  item?.goodsName ||
  item?.product_name ||
  item?.name ||
  ''
).trim()

const getGoodsItemSpec = item => String(
  item?.spec ||
  item?.specification ||
  item?.goods_spec ||
  ''
).trim()

const getGoodsItemQuantity = item => {
  if (item?.quantity === undefined || item?.quantity === null || item.quantity === '') {
    return ''
  }

  const quantity = String(item.quantity).trim()
  return quantity
}

const getGoodsItems = order => (
  Array.isArray(order?.order_goods)
    ? order.order_goods.filter(Boolean)
    : []
)

const getAllGoods = order => getGoodsItems(order)
  .map(getGoodsItemName)
  .filter(Boolean)
  .join('、')

const getAllSpecs = order => getGoodsItems(order)
  .map(getGoodsItemSpec)
  .filter(Boolean)
  .join('、')

const getAllQuantity = order => getGoodsItems(order)
  .map(getGoodsItemQuantity)
  .filter(Boolean)
  .join('、')

const getGoodsName = order => {
  const firstGoods = getFirstGoods(order)
  if (firstGoods) {
    return [getGoodsItemName(firstGoods), getGoodsItemSpec(firstGoods)]
      .filter(Boolean)
      .join(' ')
      .trim()
  }
  return String(order?.goods_name || '').replace(/\n/g, ' ').trim()
}

const getGoodsWeight = order => {
  if (order?.goods_weight) {
    return String(order.goods_weight)
  }

  const goods = Array.isArray(order?.order_goods) ? order.order_goods : []
  if (!goods.length) {
    return ''
  }

  const total = goods.reduce((sum, item) => sum + (Number(item.quantity) || 0), 0)
  return `${total}${goods[0]?.unit || 'kg'}`
}

const getGoodsQuantity = order => {
  if (order?.goods_quantity !== undefined && order?.goods_quantity !== null) {
    return String(order.goods_quantity)
  }

  if (order?.total_packages !== undefined && order?.total_packages !== null) {
    return `${Number(order.total_packages) || 0}件`
  }

  const goods = Array.isArray(order?.order_goods) ? order.order_goods : []
  if (!goods.length) {
    return ''
  }

  return `${goods.reduce((sum, item) => sum + (Number(item.packages) || 0), 0)}件`
}

const getService = order => (
  Array.isArray(order?.logistics_service)
    ? (order.logistics_service[0] || '')
    : String(order?.logistics_service || '')
)

const getShippingMethod = order => {
  const methodMap = {
    0: '物流',
    1: '零担快运',
    2: '快递',
    3: '专车',
    4: order?.shipping_custom || '其它'
  }
  if (order?.shipping_method !== undefined && order?.shipping_method !== '') {
    return methodMap[order.shipping_method] || '其它'
  }
  return order?.logistics_type || ''
}

const getFreightTotal = order => {
  if (!Array.isArray(order?.freight_costs)) {
    return ''
  }
  const total = order.freight_costs.reduce(
    (sum, item) => sum + (Number(item.amount) || 0),
    0
  )
  return total ? `¥${total.toFixed(2)}` : ''
}

export const getLogisticsCopyValues = (order, options = {}) => {
  const printVariables = options.printVariables || {}
  const storeName = [options.storeName, order?.store_name]
    .find(name => name && name !== '未知门店') ||
    (order?.type == 1 ? '绝缘' : '中固')
  const orderNumber = order?.order_number ||
    order?.orderNumber ||
    printVariables.orderNumber ||
    ''
  const customerName = order?.order_client ||
    order?.customer_name ||
    printVariables.customerName ||
    ''
  const receiverName = order?.receiver_name ||
    order?.contact_person ||
    printVariables.contactPerson ||
    ''
  const receiverPhone = order?.receiver_phone ||
    order?.contact_phone ||
    printVariables.contactPhone ||
    ''
  const receiverAddress = order?.receiver_address ||
    order?.contact_address ||
    printVariables.contactAddress ||
    ''
  const goodsName = getGoodsName(order) || printVariables.goodsName || ''
  const allGoods = getAllGoods(order) ||
    printVariables.allGoods ||
    order?.goods_name ||
    printVariables.goodsName ||
    ''
  const allSpecs = getAllSpecs(order) ||
    printVariables.allSpecs ||
    order?.goods_spec ||
    printVariables.spec ||
    ''
  const allQuantity = getAllQuantity(order) ||
    printVariables.allQuantity ||
    order?.total_quantity ||
    order?.goods_quantity ||
    printVariables.totalQuantity ||
    ''
  const goodsWeight = getGoodsWeight(order) || printVariables.totalQuantity || ''
  const goodsQuantity = getGoodsQuantity(order) ||
    (printVariables.totalPackages !== undefined
      ? `${printVariables.totalPackages}件`
      : '')
  const goodsPackaging = order?.goods_packaging ||
    printVariables.goodsPackaging ||
    ''
  const logisticsService = getService(order) ||
    printVariables.logisticsService ||
    ''
  const shippingMethod = getShippingMethod(order)
  const logisticsNo = order?.logistics_no || ''
  const shippedDate = order?.shipped_date || order?.completed_date || ''
  const freightTotal = order?.freight_total || getFreightTotal(order)
  const orderRemark = order?.remark || printVariables.orderRemark || ''

  return {
    ...printVariables,
    title: `【${storeName}订单】`,
    storeName,
    orderNumber,
    customerName,
    projectName: order?.project_name || printVariables.projectName || '',
    receiverName,
    receiverPhone,
    receiverAddress,
    goodsName,
    allGoods,
    allGoodsName: allGoods,
    allSpecs,
    allGoodsSpec: allSpecs,
    allQuantity,
    allGoodsQuantity: allQuantity,
    goodsWeight,
    goodsQuantity,
    goodsPackaging,
    logisticsService,
    shippingMethod,
    logisticsNo,
    shippedDate,
    freightTotal,
    orderRemark,
    // Keep aliases for configurations created before the variable editor upgrade.
    receiver_name: receiverName,
    receiver_phone: receiverPhone,
    receiver_address: receiverAddress,
    goods_name: goodsName,
    goods_weight: goodsWeight,
    goods_quantity: goodsQuantity,
    goods_packaging: goodsPackaging,
    logistics_service: logisticsService,
    shipping_method: shippingMethod,
    logistics_no: logisticsNo,
    shipped_date: shippedDate,
    freight_total: freightTotal,
    remark: orderRemark
  }
}

const getTemplateVariables = template => [...String(template || '').matchAll(
  /\{([^{}]+)\}|@([A-Za-z][A-Za-z0-9_]*)/g
)].map(match => match[1] || match[2])

const applyTemplate = (template, values) => String(template || '')
  .replace(/\{([^{}]+)\}|@([A-Za-z][A-Za-z0-9_]*)/g, (_match, braceKey, atKey) => {
    const key = braceKey || atKey
    return Object.prototype.hasOwnProperty.call(values, key)
      ? String(values[key] ?? '')
      : ''
  })

export const formatLogisticsOrderForCopy = (order, options = {}) => {
  const fields = normalizeLogisticsCopyFields(
    options.fields ?? getDefaultLogisticsCopyFields()
  )
  const values = getLogisticsCopyValues(order, options)

  const lines = fields
    .filter(field => field.enabled)
    .map(field => {
      const template = String(field.template || '').trim()
      const variables = getTemplateVariables(template)
      const hasValue = variables.some(key =>
        Object.prototype.hasOwnProperty.call(values, key) &&
        String(values[key] ?? '').trim()
      )
      const rendered = applyTemplate(template, values).trim()

      if (!rendered || (variables.length > 0 && !hasValue)) {
        return ''
      }
      return rendered
    })
    .filter(Boolean)

  return lines.length ? `${lines.join('\n')}\n` : ''
}

export const getLogisticsCopyPreviewOrder = () => ({
  store_name: '伟杰',
  order_number: 'ZG20260924001',
  order_client: '示例客户',
  project_name: '示例项目',
  receiver_name: '王哥哥',
  receiver_phone: '18888888888',
  receiver_address: '北京天安门大楼上',
  goods_name: '棒棒糖 30支/袋',
  goods_weight: '50公斤',
  goods_quantity: '0件',
  goods_packaging: '纸箱',
  logistics_service: '送货上门+回单拍照回传',
  shipping_method: 0,
  logistics_no: 'YT123456789',
  shipped_date: '2026-09-24',
  freight_costs: [{ amount: 15 }],
  order_goods: [],
  remark: ''
})
